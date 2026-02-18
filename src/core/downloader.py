"""
Module: downloader
Purpose: YouTube metadata and transcript downloading via yt-dlp
Created: 2026-01-28
Updated: 2026-01-29
Session: yt_trans_20260129_002 | Context: 17
"""
import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from src.core.models import VideoMeta, TranscriptEntry


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Handles:
        - youtube.com/watch?v=VIDEO_ID
        - youtu.be/VIDEO_ID
        - youtube.com/v/VIDEO_ID
        - youtube.com/embed/VIDEO_ID
        - youtube.com/shorts/VIDEO_ID
        - youtube.com/live/VIDEO_ID
        - youtube.com/live/VIDEO_ID?si=TRACKING_PARAM
        - Bare VIDEO_ID (11 characters)
    
    Returns:
        11-character video ID or None if not found
    """
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/|/live/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$"  # bare ID
    ]
    for pattern in patterns:
        if match := re.search(pattern, url.strip()):
            return match.group(1)
    return None


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    if not seconds:
        return "Unknown"
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def format_date(date_str: str) -> str:
    """Convert YYYYMMDD to YYYY-MM-DD."""
    if date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str or "Unknown"


def format_timestamp(seconds: float) -> str:
    """Format seconds as [MM:SS] timestamp."""
    total_secs = int(seconds)
    m, s = total_secs // 60, total_secs % 60
    return f"[{m:02d}:{s:02d}]"


def extract_links_from_description(description: str) -> list[dict]:
    """
    Extract URLs and their context from video description.
    
    Returns list of {"url": str, "context": str} dicts.
    Limited to 20 links.
    """
    if not description:
        return []
    
    links = []
    url_pattern = r'(https?://[^\s<>"]+)'
    
    for line in description.split('\n'):
        if urls := re.findall(url_pattern, line):
            context = re.sub(url_pattern, '', line).strip()
            for url in urls:
                links.append({
                    "url": url,
                    "context": context[:100] if context else ""
                })
    
    return links[:20]


def parse_vtt_transcript(vtt_path: Path) -> list[TranscriptEntry]:
    """
    Parse VTT file and return transcript with timestamps.
    Deduplicates repeated lines common in auto-generated subtitles.
    """
    if not vtt_path.exists():
        return []
    
    entries = []
    current_time = None
    seen_text = set()
    
    for line in vtt_path.read_text(errors='replace').split('\n'):
        line = line.strip()
        
        # Skip metadata
        if not line or line.startswith(('WEBVTT', 'Kind:', 'Language:')) or line.isdigit():
            continue
        
        # Parse timestamp line: "00:00:05.520 --> 00:00:08.160"
        if '-->' in line:
            time_match = re.match(r'(\d+):(\d+):(\d+)\.(\d+)', line)
            if time_match:
                h, m, s = int(time_match.group(1)), int(time_match.group(2)), int(time_match.group(3))
                current_time = h * 3600 + m * 60 + s
            continue
        
        # Clean HTML tags and normalize text
        clean = re.sub(r'<[^>]+>', '', line)
        if clean and clean not in seen_text:
            seen_text.add(clean)
            entries.append(TranscriptEntry(
                timestamp=format_timestamp(current_time) if current_time is not None else "[00:00]",
                text=clean
            ))
    
    return entries


def fetch_metadata(url: str) -> Optional[VideoMeta]:
    """
    Fetch video metadata from YouTube using yt-dlp.
    Does NOT download transcript yet - just metadata for preview.
    
    Returns:
        VideoMeta with raw metadata and proposed naming values,
        or None if fetch fails.
    """
    vid = extract_video_id(url)
    if not vid:
        return None
    
    tmp_base = f"/tmp/yt_meta_{vid}"
    
    cmd = [
        "yt-dlp",
        "--write-info-json",
        "--skip-download",
        "--no-write-playlist-metafiles",
        "-o", tmp_base,
        f"https://youtube.com/watch?v={vid}"
    ]
    
    proc = subprocess.run(cmd, capture_output=True, text=True)
    
    json_file = Path(f"{tmp_base}.info.json")
    
    if not json_file.exists():
        return None
    
    try:
        meta = json.loads(json_file.read_text())
    finally:
        # Cleanup
        if json_file.exists():
            json_file.unlink()
    
    return VideoMeta(
        video_id=vid,
        url=url,
        title=meta.get("title", "Untitled"),
        channel=meta.get("channel") or meta.get("uploader", "Unknown"),
        channel_url=meta.get("channel_url", ""),
        upload_date=meta.get("upload_date", ""),
        upload_date_formatted=format_date(meta.get("upload_date", "")),
        duration=meta.get("duration", 0),
        duration_formatted=format_duration(meta.get("duration")),
        view_count=meta.get("view_count", 0),
        like_count=meta.get("like_count", 0),
        channel_follower_count=meta.get("channel_follower_count", 0),
        description=meta.get("description", ""),
        chapters=meta.get("chapters") or [],
    )


def fetch_transcript(video: VideoMeta, include_links: bool = True) -> VideoMeta:
    """
    Fetch transcript for a video that already has metadata.
    Updates the video object in place with transcript and links.
    
    Returns:
        Updated VideoMeta with transcript populated.
    """
    vid = video.video_id
    tmp_base = f"/tmp/yt_trans_{vid}"
    
    cmd = [
        "yt-dlp",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        "-o", tmp_base,
        f"https://youtube.com/watch?v={vid}"
    ]
    
    subprocess.run(cmd, capture_output=True, text=True)
    
    vtt_file = Path(f"{tmp_base}.en.vtt")
    
    # Parse transcript
    video.transcript = parse_vtt_transcript(vtt_file)
    
    # Extract links from description
    if include_links:
        video.links = extract_links_from_description(video.description)
    
    # Cleanup
    if vtt_file.exists():
        vtt_file.unlink()
    
    return video
