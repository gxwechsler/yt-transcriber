# Governance — YT Transcriber

**Constitutional authority:** [Architext_Repo](https://github.com/gxwechsler/Architext_Repo)
**Repository:** `gxwechsler/yt-transcriber`
**Created:** 2026-02-18


---


## Scope

YT Transcriber is a Streamlit application for downloading YouTube transcripts with metadata review and custom naming. It produces Markdown, Word, and JSON output organized by author.


## Local Rules

1. **External dependency:** This app depends on `yt-dlp` as a system-level tool. Any changes to download logic must be tested against current yt-dlp behavior before merge.
2. **Output formats are stable.** The three-format output (`.md`, `.docx`, `.json`) is a design commitment. New formats may be added; existing formats must not be removed without a recorded decision.
3. **No credentials in source.** API keys, tokens, or user-specific paths must never appear in committed files.
4. **`gzpqb_utils` is optional.** The app must always function without the shared utility library. Fallback implementations are mandatory for any imported function.


## Clawdio Permissions

| Capability   | Status | Notes                                      |
|--------------|--------|--------------------------------------------|
| Read         | ✓      | Full repository access                     |
| Issues       | ✓      | May raise issues autonomously              |
| Execute      | ✓*     | Requires prior validation by Guillermo     |
| Pull Request | —      | Not yet granted                            |
| Merge        | —      | Reserved to sovereign layer                |

**Phase:** Executor


## Amendment Log

| Date       | Change                        | Authority |
|------------|-------------------------------|-----------|
| 2026-02-18 | Repository created. Initial governance established. | gxwechsler |
