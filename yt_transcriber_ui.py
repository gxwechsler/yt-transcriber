#!/usr/bin/env python3
"""
Module: yt_transcriber_ui
Purpose: Streamlit interface for YouTube transcript extraction with metadata review
Created: 2026-01-28
Session: yt_trans_20260128_001 | Context: 1

Workflow:
    1. Input: User pastes URL(s)
    2. Fetch: Download metadata from YouTube
    3. Review: User edits Author/Topic/Year in table
    4. Save: Download transcripts and write files with approved naming
"""
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import streamlit as st
import pandas as pd
from datetime import datetime

from src.core.models import VideoMeta, ProcessResult, BatchState
from src.core.downloader import extract_video_id, fetch_metadata, fetch_transcript
from src.core.writers import write_markdown, write_docx, write_json
from src.utils.filename import build_filename, build_output_path

# Try to import shared utilities
try:
    from gzpqb_utils import load_config, expand_path, ImpactMetrics, render_compact_metrics
    HAS_GZPQB_UTILS = True
except ImportError:
    HAS_GZPQB_UTILS = False
    # Fallback config loading
    def load_config(name, config_dir=None):
        config_dir = config_dir or PROJECT_ROOT / "config"
        with open(config_dir / f"{name}.json") as f:
            return json.load(f)
    
    def expand_path(path):
        import os
        return Path(os.path.expanduser(str(path))).resolve()


# === LOAD CONFIG ===
CONFIG = load_config("settings", PROJECT_ROOT / "config")
OUTPUT_BASE = CONFIG.get("output_base", "~/My_Drive_Mirror/024_YT_TRANSCRIPTIONS")
FILENAME_MAX_LENGTH = CONFIG.get("filename_max_length", 50)
BATCH_MAX_SIZE = CONFIG.get("batch_max_size", 10)


# === SESSION STATE INITIALIZATION ===
def init_session_state():
    """Initialize Streamlit session state."""
    if "phase" not in st.session_state:
        st.session_state.phase = "input"
    if "pending_videos" not in st.session_state:
        st.session_state.pending_videos = []
    if "results" not in st.session_state:
        st.session_state.results = []
    if "metrics" not in st.session_state and HAS_GZPQB_UTILS:
        st.session_state.metrics = ImpactMetrics(
            session_id=f"yt_trans_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )


def reset_state():
    """Reset to input phase."""
    st.session_state.phase = "input"
    st.session_state.pending_videos = []
    st.session_state.results = []


# === PROCESSING FUNCTIONS ===
def process_and_save_video(video: VideoMeta, output_base: str, include_links: bool) -> ProcessResult:
    """
    Fetch transcript and save files for a single video.
    Uses the approved author/topic/year for naming.
    """
    result = ProcessResult(
        video_id=video.video_id,
        url=video.url,
        status="error"
    )
    
    try:
        # Fetch transcript
        video = fetch_transcript(video, include_links=include_links)
        
        # Build filename from approved values
        filename = build_filename(
            video.proposed_author,
            video.proposed_topic,
            video.proposed_year,
            max_length=FILENAME_MAX_LENGTH
        )
        
        # Write files
        files = []
        
        md_path = build_output_path(output_base, video.proposed_author, filename, "md")
        write_markdown(video, md_path)
        files.append(str(md_path))
        
        docx_path = build_output_path(output_base, video.proposed_author, filename, "docx")
        write_docx(video, docx_path)
        files.append(str(docx_path))
        
        json_path = build_output_path(output_base, video.proposed_author, filename, "json")
        write_json(video, json_path)
        files.append(str(json_path))
        
        result.status = "success"
        result.message = f"Saved: {filename}"
        result.title = video.title
        result.files = files
        
    except Exception as e:
        result.message = str(e)
    
    return result


# === UI COMPONENTS ===
def render_input_phase():
    """Render URL input interface."""
    st.header("📺 YT Transcriber")
    st.caption("Download YouTube transcripts with custom naming")
    
    # URL input
    urls_text = st.text_area(
        "YouTube URLs (one per line)",
        height=150,
        placeholder="https://youtube.com/watch?v=abc123\nhttps://youtu.be/def456",
        help=f"Maximum {BATCH_MAX_SIZE} URLs per batch"
    )
    
    # Parse URLs
    urls = []
    if urls_text:
        urls = [u.strip() for u in urls_text.strip().split('\n') if u.strip()]
        valid_urls = [u for u in urls if extract_video_id(u)]
        
        if valid_urls:
            st.caption(f"✓ {len(valid_urls)} valid URL(s) detected")
            if len(valid_urls) > BATCH_MAX_SIZE:
                st.warning(f"Maximum {BATCH_MAX_SIZE} URLs. Only first {BATCH_MAX_SIZE} will be processed.")
                valid_urls = valid_urls[:BATCH_MAX_SIZE]
        elif urls:
            st.warning("No valid YouTube URLs detected")
            valid_urls = []
    else:
        valid_urls = []
    
    # Fetch button
    col1, col2 = st.columns([1, 4])
    with col1:
        fetch_btn = st.button(
            "🔍 Fetch Metadata",
            type="primary",
            disabled=not valid_urls
        )
    
    if fetch_btn and valid_urls:
        with st.spinner(f"Fetching metadata for {len(valid_urls)} video(s)..."):
            videos = []
            progress = st.progress(0)
            
            for i, url in enumerate(valid_urls):
                meta = fetch_metadata(url)
                if meta:
                    videos.append(meta)
                progress.progress((i + 1) / len(valid_urls))
            
            progress.empty()
        
        if videos:
            st.session_state.pending_videos = videos
            st.session_state.phase = "review"
            st.rerun()
        else:
            st.error("Could not fetch metadata for any videos")


def render_review_phase():
    """Render metadata review table with editable fields."""
    st.header("📝 Review & Edit Metadata")
    st.caption("Edit Author, Topic, and Year before saving. Uncheck rows to skip.")
    
    videos = st.session_state.pending_videos
    
    # Build dataframe for editing
    data = []
    for v in videos:
        data.append({
            "Select": v.selected,
            "Author": v.proposed_author,
            "Topic": v.proposed_topic,
            "Year": v.proposed_year,
            "Original Title": v.title[:60] + "..." if len(v.title) > 60 else v.title,
            "Channel": v.channel,
            "_idx": videos.index(v)  # Hidden index for tracking
        })
    
    df = pd.DataFrame(data)
    
    # Editable table
    edited_df = st.data_editor(
        df,
        column_config={
            "Select": st.column_config.CheckboxColumn("✓", default=True, width="small"),
            "Author": st.column_config.TextColumn("Author", width="medium"),
            "Topic": st.column_config.TextColumn("Topic", width="large"),
            "Year": st.column_config.TextColumn("Year", width="small"),
            "Original Title": st.column_config.TextColumn("Original Title", disabled=True, width="large"),
            "Channel": st.column_config.TextColumn("Channel", disabled=True, width="medium"),
            "_idx": None  # Hide index column
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )
    
    # Update videos with edited values
    for i, row in edited_df.iterrows():
        idx = row["_idx"]
        videos[idx].selected = row["Select"]
        videos[idx].proposed_author = row["Author"]
        videos[idx].proposed_topic = row["Topic"]
        videos[idx].proposed_year = str(row["Year"])
    
    # Count selected
    selected_count = sum(1 for v in videos if v.selected)
    
    # Preview filename
    if selected_count > 0:
        st.divider()
        st.subheader("Preview")
        for v in videos:
            if v.selected:
                filename = build_filename(v.proposed_author, v.proposed_topic, v.proposed_year)
                st.code(f"{v.proposed_author}/{filename}.{{md,docx,json}}")
    
    # Action buttons
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        back_btn = st.button("← Back", use_container_width=True)
    
    with col2:
        save_btn = st.button(
            f"💾 Save {selected_count} Video(s)",
            type="primary",
            disabled=selected_count == 0,
            use_container_width=True
        )
    
    if back_btn:
        reset_state()
        st.rerun()
    
    if save_btn:
        st.session_state.phase = "processing"
        st.rerun()


def render_processing_phase():
    """Process selected videos and save files."""
    st.header("⏳ Processing...")
    
    videos = [v for v in st.session_state.pending_videos if v.selected]
    include_links = CONFIG.get("include_links_default", True)
    
    results = []
    progress = st.progress(0)
    status = st.empty()
    
    for i, video in enumerate(videos):
        status.text(f"Processing {i+1}/{len(videos)}: {video.title[:50]}...")
        
        result = process_and_save_video(video, OUTPUT_BASE, include_links)
        results.append(result)
        
        # Update metrics if available
        if HAS_GZPQB_UTILS and "metrics" in st.session_state:
            if result.is_success:
                st.session_state.metrics.record_task_success()
                st.session_state.metrics.files_created += 3  # md, docx, json
            else:
                st.session_state.metrics.record_task_failure()
        
        progress.progress((i + 1) / len(videos))
    
    progress.empty()
    status.empty()
    
    st.session_state.results = results
    st.session_state.phase = "complete"
    st.rerun()


def render_complete_phase():
    """Show completion summary."""
    st.header("✅ Complete")
    
    results = st.session_state.results
    success = [r for r in results if r.is_success]
    failed = [r for r in results if not r.is_success]
    
    # Summary metrics
    if HAS_GZPQB_UTILS and "metrics" in st.session_state:
        render_compact_metrics(st.session_state.metrics)
    
    # Success summary
    if success:
        st.success(f"✅ {len(success)} video(s) saved successfully")
        
        with st.expander("Show saved files", expanded=True):
            for r in success:
                st.markdown(f"**{r.title}**")
                for f in r.files:
                    st.code(f, language=None)
    
    # Failure summary
    if failed:
        st.error(f"❌ {len(failed)} video(s) failed")
        
        with st.expander("Show errors"):
            for r in failed:
                st.write(f"• {r.url}: {r.message}")
    
    # Output location
    st.divider()
    st.info(f"📁 Output folder: `{expand_path(OUTPUT_BASE)}`")
    
    # New batch button
    if st.button("🔄 Process New Batch", type="primary"):
        reset_state()
        st.rerun()


# === SIDEBAR ===
def render_sidebar():
    """Render settings sidebar."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.text_input(
            "Output Directory",
            value=OUTPUT_BASE,
            disabled=True,
            help="Configure in config/settings.json"
        )
        
        st.divider()
        
        st.caption("**Output Format**")
        st.caption("• `.md` — Markdown transcript")
        st.caption("• `.docx` — Word document")
        st.caption("• `.json` — Structured metadata")
        
        st.divider()
        
        st.caption("**Naming Pattern**")
        st.caption("`{Author}/{Author}_{Topic}_{Year}.ext`")
        
        st.divider()
        
        # Phase indicator
        phase_labels = {
            "input": "1️⃣ Input URLs",
            "review": "2️⃣ Review Metadata",
            "processing": "3️⃣ Processing...",
            "complete": "4️⃣ Complete"
        }
        st.caption(f"**Current Phase:** {phase_labels.get(st.session_state.phase, '?')}")


# === MAIN ===
def main():
    st.set_page_config(
        page_title="YT Transcriber",
        page_icon="📺",
        layout="wide"
    )
    
    init_session_state()
    render_sidebar()
    
    # Route to current phase
    phase = st.session_state.phase
    
    if phase == "input":
        render_input_phase()
    elif phase == "review":
        render_review_phase()
    elif phase == "processing":
        render_processing_phase()
    elif phase == "complete":
        render_complete_phase()
    else:
        st.error(f"Unknown phase: {phase}")
        reset_state()


if __name__ == "__main__":
    main()
