# YT Transcriber — Architecture

**Version:** 2.0  
**Updated:** 2026-01-28  
**Session:** yt_trans_20260128_001 | Context: 1

---

## Overview

Streamlit app for downloading YouTube transcripts with user-controlled naming. Two-phase workflow: fetch metadata first, review/edit naming fields, then save.

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │ ──▶ │   FETCH     │ ──▶ │   REVIEW    │ ──▶ │    SAVE     │
│  Paste URLs │     │  Metadata   │     │ Edit table  │     │   Files     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

1. **Input**: User pastes YouTube URL(s)
2. **Fetch**: yt-dlp retrieves metadata (title, channel, date, etc.)
3. **Review**: Editable table shows proposed Author/Topic/Year with raw data for reference
4. **Save**: Approved naming used for files; transcripts fetched and written

## File Structure

```
yt_transcriber/
├── config/
│   └── settings.json          # App configuration
├── src/
│   ├── core/
│   │   ├── models.py          # VideoMeta, ProcessResult, BatchState
│   │   ├── downloader.py      # yt-dlp wrapper
│   │   └── writers.py         # Markdown, Word, JSON writers
│   └── utils/
│       └── filename.py        # Filename/path builders
├── docs/
│   ├── SESSION_CONTEXT.json   # Claude session state
│   └── architecture.md        # This file
├── requirements.txt
└── yt_transcriber_ui.py       # Streamlit entry point
```

## Data Flow

```
URL(s)
  │
  ▼
┌─────────────────┐
│ fetch_metadata  │  ← yt-dlp --write-info-json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   VideoMeta     │  ← Proposed author/topic/year set from raw data
└────────┬────────┘
         │
    [User edits]
         │
         ▼
┌─────────────────┐
│ fetch_transcript│  ← yt-dlp --write-auto-sub
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Writers      │  ← write_markdown, write_docx, write_json
└────────┬────────┘
         │
         ▼
{Author}/{Author}_{Topic}_{Year}.{md,docx,json}
```

## Key Components

### VideoMeta (models.py)
Central data model containing:
- Raw yt-dlp fields: `title`, `channel`, `upload_date`, `duration`, etc.
- Proposed naming: `proposed_author`, `proposed_topic`, `proposed_year`
- Processing state: `selected`, `transcript`, `links`, `chapters`

### Downloader (downloader.py)
Two-stage fetching:
1. `fetch_metadata(url)` → Quick metadata only (for preview)
2. `fetch_transcript(video)` → Subtitle download (slower)

### Writers (writers.py)
Three output formats, all receiving `VideoMeta`:
- `write_markdown()` → Timestamped text with metadata header
- `write_docx()` → Formatted Word document
- `write_json()` → Structured data for programmatic use

### Filename Utils (filename.py)
- `build_filename(author, topic, year)` → Sanitized `Author_Topic_Year`
- `build_output_path(base, author, filename, ext)` → Creates subfolder

## Configuration

`config/settings.json`:
```json
{
    "output_base": "~/My_Drive_Mirror/024_YT_TRANSCRIPTIONS",
    "filename_max_length": 50,
    "batch_max_size": 10,
    "include_links_default": true,
    "subfolder_by": "author"
}
```

## External Dependencies

### gzpqb_utils (shared package)
- `ImpactMetrics` — Triple-reading metrics tracking
- `load_config()` — JSON configuration loading
- `sanitize_for_filename()` — Filesystem-safe string conversion

Install: `pip install -e ~/Organic_Apps/gzpqb_utils`

### yt-dlp
- Requires nightly build for latest YouTube compatibility
- Requires Deno runtime

```bash
brew install deno
pip install -U "yt-dlp[default]" --pre --break-system-packages
```

## Output Structure

```
~/My_Drive_Mirror/024_YT_TRANSCRIPTIONS/
├── Jordan_Peterson/
│   ├── Jordan_Peterson_Maps_of_Meaning_2017.md
│   ├── Jordan_Peterson_Maps_of_Meaning_2017.docx
│   └── Jordan_Peterson_Maps_of_Meaning_2017.json
├── Iain_McGilchrist/
│   └── ...
└── Lex_Fridman/
    └── ...
```

---

*Architecture documentation. Update with significant changes.*
