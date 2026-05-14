# translate-ai-pdf

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/dozken/translate-ai-pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/dozken/translate-ai-pdf/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Streamlit web app that extracts text from PDF files, estimates translation costs across LLM providers, and translates documents using Google Gemini with real-time streaming and resumable progress.

## Demo

Upload a PDF → see token counts and cost estimates across providers → translate with live streaming → download the translated PDF.

![App screenshot placeholder](docs/screenshot.png)

## Features

- **Cost estimation** — compare translation cost across OpenAI, Anthropic, Google, DeepL, and local models before spending a dollar
- **Streaming translation** — watch output appear paragraph-by-paragraph in real-time via Gemini's streaming API
- **Resumable jobs** — SQLite-backed progress storage lets you resume an interrupted translation exactly where it stopped
- **Parallel translation** — configurable thread pool translates multiple paragraphs concurrently
- **Smart paragraph splitting** — multi-strategy splitter handles PDF text without proper paragraph breaks, with verse grouping for religious/classical texts
- **PDF output** — ReportLab-generated PDF with full Unicode/Cyrillic support and automatic font fallback
- **Multi-language UI** — English and Russian interface

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Translation API | Google Gemini (`google-generativeai`) |
| PDF parsing | pdfplumber |
| Token counting | tiktoken (exact for OpenAI, approximate for others) |
| PDF generation | ReportLab |
| Progress storage | SQLite (thread-safe via WAL mode) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` |
| Config | python-dotenv |

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/dozken/translate-ai-pdf.git
cd translate-ai-pdf
make setup

# 2. Add your API key
cp .env.example .env
# Edit .env — set GOOGLE_API_KEY

# 3. Run
make run
```

App opens at `http://localhost:8501`.

## Project Structure

```
translate-ai-pdf/
├── app.py                      # Streamlit UI (upload, cost table, streaming translation)
├── config.py                   # Env-based config with validation
├── constants.py                # App-wide constants
├── translations.py             # i18n strings (EN/RU)
├── utils/
│   ├── pdf_processor.py        # PDF text extraction via pdfplumber
│   ├── token_calculator.py     # Token counting for all providers
│   ├── cost_calculator.py      # Per-provider cost estimates
│   ├── translator.py           # Paragraph splitting + Gemini translation
│   ├── pdf_generator.py        # ReportLab PDF output with Unicode fonts
│   ├── progress_storage.py     # SQLite-backed resume storage
│   └── logger_config.py        # Rotating file + console logging
├── tests/                      # Test suite + manual scripts
├── docs/                       # Research notes and benchmarks
├── pyproject.toml
└── Makefile                    # setup / run / test / lint targets
```

## Configuration

All settings via `.env`:

```env
GOOGLE_API_KEY=your_key_here

# Translation
SOURCE_LANGUAGE=Arabic
TARGET_LANGUAGE=Russian
GEMINI_MODEL=gemini-1.5-flash

# Performance
MAX_WORKERS=5
MAX_RETRIES=3
TRANSLATION_DELAY_SECONDS=0.5

# Optional
PDF_OUTPUT_DIR=./outputs
LOG_LEVEL=INFO
```

### Supported models

- `gemini-1.5-flash` (fast, cheap — recommended)
- `gemini-1.5-pro` (higher quality)
- Token counting available for OpenAI GPT-4/3.5, Anthropic Claude, DeepL (translation not yet wired)

## Development

```bash
# Install with dev deps
pip install -e ".[dev]"

# Format + lint
make check

# Run unit tests
python -m pytest tests/ -v

# Validate API key
make test-api-key

# End-to-end translation test (requires .env)
make test-translation
```

## Architecture Notes

**Paragraph splitting** uses a four-strategy cascade: double-newline split → single-newline with heuristics → sentence-boundary grouping → word-count chunking. Each strategy targets 70–80% of the max paragraph size to balance API efficiency against translation quality. Verse-numbered content (e.g., Quran surahs) is grouped before splitting to prevent over-segmentation.

**Resume logic** hashes the PDF content to produce a stable `file_id`, then stores per-paragraph translations in SQLite. On restart, already-translated paragraphs are loaded from the database; only missing ones are sent to the API.

**Streaming** uses Gemini's streaming API with a per-paragraph callback that updates a Streamlit placeholder in real-time. The Streamlit script context is propagated into worker threads via `add_script_run_ctx`.

## License

MIT — see [LICENSE](LICENSE).
