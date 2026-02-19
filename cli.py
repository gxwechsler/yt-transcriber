#!/usr/bin/env python3
"""
Module: cli
Purpose: Command-line interface for YouTube transcript extraction
Created: 2026-02-18

Usage:
    python cli.py <url> [url2 url3 ...]
    python cli.py --from-file urls.txt
    python cli.py <url> --author "Name" --topic "Subject" --year "2024"
    python cli.py <url> --output-dir ~/transcripts
"""
import sys
import argparse
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import json

from src.core.models import VideoMeta
from src.core.downloader import extract_video_id, fetch_metadata, fetch_transcript
from src.core.writers import write_markdown, write_docx, write_json
from src.utils.filename import build_filename, build_output_path

# Try to import shared utilities
try:
    from gzpqb_utils import load_config, expand_path
except ImportError:
    def load_config(name, config_dir=None):
        config_dir = config_dir or PROJECT_ROOT / "config"
        with open(config_dir / f"{name}.json") as f:
            return json.load(f)

    def expand_path(path):
        import os
        return Path(os.path.expanduser(str(path))).resolve()


def load_output_base(override=None):
    """Resolve output directory from override or config."""
    if override:
        return str(expand_path(override))
    config = load_config("settings", PROJECT_ROOT / "config")
    return config.get("output_base", "~/transcripts")


def process_single(url, output_base, author_override=None, topic_override=None,
                    year_override=None, include_links=True):
    """
    Process a single URL through the v2 pipeline.
    Returns True on success, False on failure.
    """
    vid = extract_video_id(url)
    if not vid:
        print(f"ERROR: Invalid YouTube URL: {url}", file=sys.stderr)
        return False

    # Fetch metadata
    print(f"Fetching metadata: {url}")
    video = fetch_metadata(url)
    if not video:
        print(f"ERROR: Could not fetch metadata for {url}", file=sys.stderr)
        return False

    # Apply overrides
    if author_override:
        video.proposed_author = author_override
    if topic_override:
        video.proposed_topic = topic_override
    if year_override:
        video.proposed_year = year_override

    # Fetch transcript
    print(f"Fetching transcript: {video.title}")
    video = fetch_transcript(video, include_links=include_links)

    # Build filename
    config = load_config("settings", PROJECT_ROOT / "config")
    max_length = config.get("filename_max_length", 50)
    filename = build_filename(
        video.proposed_author,
        video.proposed_topic,
        video.proposed_year,
        max_length=max_length
    )

    # Write all three formats
    md_path = build_output_path(output_base, video.proposed_author, filename, "md")
    write_markdown(video, md_path)

    docx_path = build_output_path(output_base, video.proposed_author, filename, "docx")
    write_docx(video, docx_path)

    json_path = build_output_path(output_base, video.proposed_author, filename, "json")
    write_json(video, json_path)

    print(f"Saved: {md_path}")
    print(f"Saved: {docx_path}")
    print(f"Saved: {json_path}")

    return True


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download YouTube transcripts with custom naming."
    )

    parser.add_argument(
        "urls",
        nargs="*",
        help="YouTube URL(s) to transcribe"
    )
    parser.add_argument(
        "--from-file",
        type=str,
        help="Path to text file with one URL per line"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override output directory (default: from config/settings.json)"
    )
    parser.add_argument(
        "--author",
        type=str,
        default=None,
        help="Override proposed author (single URL only)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Override proposed topic (single URL only)"
    )
    parser.add_argument(
        "--year",
        type=str,
        default=None,
        help="Override proposed year (single URL only)"
    )
    parser.add_argument(
        "--no-links",
        action="store_true",
        help="Exclude links from video description"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Collect URLs
    urls = list(args.urls) if args.urls else []

    if args.from_file:
        file_path = Path(args.from_file)
        if not file_path.exists():
            print(f"ERROR: File not found: {args.from_file}", file=sys.stderr)
            sys.exit(1)
        file_urls = [
            line.strip() for line in file_path.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        urls.extend(file_urls)

    if not urls:
        print("ERROR: No URLs provided. Pass URLs as arguments or use --from-file.", file=sys.stderr)
        sys.exit(1)

    # Override flags only apply to single URL
    if len(urls) > 1 and any([args.author, args.topic, args.year]):
        print("WARNING: --author, --topic, --year overrides ignored for batch processing.",
              file=sys.stderr)

    output_base = load_output_base(args.output_dir)
    include_links = not args.no_links

    success_count = 0
    fail_count = 0

    for url in urls:
        overrides = {}
        if len(urls) == 1:
            overrides = {
                "author_override": args.author,
                "topic_override": args.topic,
                "year_override": args.year,
            }

        ok = process_single(url, output_base, include_links=include_links, **overrides)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print(f"\nComplete: {success_count} succeeded, {fail_count} failed.")
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
