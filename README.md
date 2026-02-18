# YT Transcriber

Streamlit application for downloading YouTube transcripts with metadata review and custom naming.


## Status

Working for single-URL processing. Batch UI implemented. Planned enhancements: batch mode improvements, better headers, date formatting, cleaner filenames, diarization.


## Setup

```bash
git clone https://github.com/gxwechsler/yt-transcriber.git
cd yt-transcriber

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

brew install deno
pip install -U "yt-dlp[default]" --pre

streamlit run yt_transcriber_ui.py
```


## Workflow

1. **Paste URLs** — single or batch, up to 10
2. **Fetch Metadata** — pulls title, channel, date from YouTube via yt-dlp
3. **Review Table** — edit Author, Topic, Year inline; uncheck to skip
4. **Save** — downloads transcripts, writes files with approved naming


## Output

Files saved to the configured output directory, organized by author:

```
{output_base}/{Author}/{Author}_{Topic}_{Year}.md
{output_base}/{Author}/{Author}_{Topic}_{Year}.docx
{output_base}/{Author}/{Author}_{Topic}_{Year}.json
```

| Format  | Contents                                         |
|---------|--------------------------------------------------|
| `.md`   | Markdown with metadata header and timestamped transcript |
| `.docx` | Formatted Word document                          |
| `.json` | Structured metadata for programmatic use         |


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


## Project Structure

```
yt-transcriber/
├── config/
│   └── settings.json            # Runtime configuration
├── src/
│   ├── core/
│   │   ├── models.py            # VideoMeta, ProcessResult, BatchState
│   │   ├── downloader.py        # yt-dlp wrapper (metadata + transcript fetch)
│   │   └── writers.py           # File writers (Markdown, Word, JSON)
│   └── utils/
│       └── filename.py          # Filename and path building
├── docs/
│   ├── architecture.md          # Architecture documentation
│   └── SESSION_CONTEXT.json     # Development session state
├── yt_transcriber_ui.py         # Streamlit entry point
├── requirements.txt             # Python dependencies
├── GOVERNANCE.md                # Repository governance (Architexture)
└── .gitignore
```


## Dependencies

- **Python 3.11+**
- **yt-dlp** — YouTube metadata and subtitle download (requires nightly build)
- **Deno** — required by yt-dlp for some extraction
- **Streamlit** — web interface
- **python-docx** — Word document generation
- **pandas** — data handling in review table
- **gzpqb_utils** *(optional)* — shared utility library for metrics tracking. The app functions fully without it; fallback implementations are included.


## Troubleshooting

**"No supported JavaScript runtime"** — Install Deno: `brew install deno`

**"SABR streaming" or format errors** — Update yt-dlp: `pip install -U "yt-dlp[default]" --pre`

**No transcript in output** — The video may not have English auto-generated subtitles.


## Governance

This repository operates under the [Architexture](https://github.com/gxwechsler/Architext_Repo) governance framework. See `GOVERNANCE.md` for local rules, Clawdio permissions, and amendment history.


---

*Version 2.0 — 2026-02-18*
