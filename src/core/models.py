"""
Module: models
Purpose: Data models for YT Transcriber
Created: 2026-01-28
Session: yt_trans_20260128_001 | Context: 1
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class VideoMeta:
    """
    Metadata for a YouTube video.
    Contains both raw yt-dlp data and proposed naming values.
    """
    # Core identifiers
    video_id: str
    url: str
    
    # Raw metadata from yt-dlp
    title: str = "Untitled"
    channel: str = "Unknown"
    channel_url: str = ""
    upload_date: str = ""  # YYYYMMDD format
    upload_date_formatted: str = ""  # YYYY-MM-DD
    duration: int = 0
    duration_formatted: str = ""
    view_count: int = 0
    like_count: int = 0
    channel_follower_count: int = 0
    description: str = ""
    
    # Proposed naming (editable by user)
    proposed_author: str = ""
    proposed_topic: str = ""
    proposed_year: str = ""
    
    # Chapters and links
    chapters: list = field(default_factory=list)
    links: list = field(default_factory=list)
    
    # Processing state
    selected: bool = True  # For batch selection
    transcript: list = field(default_factory=list)
    
    def __post_init__(self):
        """Set proposed values from raw metadata if not already set."""
        if not self.proposed_author:
            self.proposed_author = self.channel or "Unknown"
        if not self.proposed_topic:
            self.proposed_topic = self._clean_title_for_topic()
        if not self.proposed_year:
            self.proposed_year = self.upload_date[:4] if len(self.upload_date) >= 4 else "Unknown"
    
    def _clean_title_for_topic(self) -> str:
        """Extract a clean topic from title."""
        import re
        topic = self.title
        # Remove common prefixes like "EP 123:" or "#45"
        topic = re.sub(r'^(EP\.?\s*\d+[:\s-]*|#\d+[:\s-]*)', '', topic, flags=re.IGNORECASE)
        # Remove channel name if it appears in title
        if self.channel and self.channel.lower() in topic.lower():
            topic = re.sub(re.escape(self.channel), '', topic, flags=re.IGNORECASE)
        return topic.strip()[:100] or "Untitled"


@dataclass
class TranscriptEntry:
    """Single transcript entry with timestamp."""
    timestamp: str  # "[MM:SS]" format
    text: str


@dataclass
class ProcessResult:
    """Result of processing a video."""
    video_id: str
    url: str
    status: str  # "success" | "error" | "skipped"
    message: str = ""
    title: str = ""
    files: list = field(default_factory=list)
    
    @property
    def is_success(self) -> bool:
        return self.status == "success"


@dataclass
class BatchState:
    """
    State container for batch processing workflow.
    Tracks phase and pending videos.
    """
    phase: str = "input"  # "input" | "review" | "processing" | "complete"
    pending_videos: list = field(default_factory=list)  # List[VideoMeta]
    results: list = field(default_factory=list)  # List[ProcessResult]
    
    def reset(self):
        """Reset to initial state."""
        self.phase = "input"
        self.pending_videos = []
        self.results = []
    
    def to_review(self, videos: list):
        """Transition to review phase with fetched videos."""
        self.pending_videos = videos
        self.phase = "review"
    
    def to_processing(self):
        """Transition to processing phase."""
        self.phase = "processing"
        self.results = []
    
    def to_complete(self, results: list):
        """Transition to complete phase with results."""
        self.results = results
        self.phase = "complete"
