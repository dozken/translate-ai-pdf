# LLM Translate - PDF Translation Cost Calculator

Web-based PDF translation cost calculator built with Streamlit and Python. Calculate translation costs across multiple LLM providers before committing to a translation.

## Features

- 📄 **PDF Processing**: Extract text from PDF files using pdfplumber
- 📊 **Token Counting**: Calculate token counts for all major LLM providers (free, local)
- 💰 **Cost Comparison**: Compare translation costs across providers with detailed breakdowns
- 🌐 **Translation**: Translate Arabic PDFs to Russian using Google Gemini API
- 📄 **PDF Output**: Generate translated PDFs with proper formatting and Unicode support
- 💾 **Progress Saving**: Resume interrupted translations with SQLite-based progress tracking
- 🚀 **Real-time Streaming**: Watch translations appear in real-time with live progress updates
- 🌍 **Multi-language**: English and Russian UI support

## Architecture

- **Frontend**: Streamlit web interface
- **Backend**: Python 3.8+
- **PDF Processing**: pdfplumber
- **Token Counting**: tiktoken (exact for OpenAI, approximate for others)
- **Translation API**: Google Gemini (via google-generativeai)
- **PDF Generation**: ReportLab with Unicode font support
- **Progress Storage**: SQLite with thread-safe access
- **Logging**: Structured logging with rotation

## Prerequisites

- Python 3.8+ - Install from https://python.org/
- pip (usually comes with Python)
- Google AI Studio API key for Gemini

## Setup

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

3. **Run in development:**
   ```bash
   streamlit run app.py
   ```

4. **Run tests (optional):**
   ```bash
   python -m pytest tests/
   ```

## Project Structure

```
LLMTranslate/
├── app.py                  # Main Streamlit application
├── config.py              # Configuration management
├── constants.py           # Application constants
├── translations.py        # Multi-language support
├── utils/                 # Utility modules
│   ├── pdf_processor.py   # PDF text extraction
│   ├── token_calculator.py # Token counting for all providers
│   ├── cost_calculator.py  # Cost estimation
│   ├── translator.py       # Translation logic
│   ├── pdf_generator.py    # PDF generation with Unicode support
│   ├── progress_storage.py # SQLite progress tracking
│   └── logger_config.py    # Logging configuration
├── tests/                 # Test suite
├── utils/experimental/    # Experimental features
├── docs/                  # Documentation
├── progress/             # SQLite database storage
├── logs/                 # Application logs
├── pyproject.toml        # Python package configuration
├── .env.example          # Environment template
└── README.md
```

## Usage

1. Launch the application: `streamlit run app.py`
2. Upload a PDF file (Arabic text recommended)
3. View token counts and cost estimates across all providers
4. Select a provider (currently Google Gemini is implemented)
5. Start translation with real-time progress tracking
6. Download the translated PDF

## Configuration

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key_here
SOURCE_LANGUAGE=Arabic
TARGET_LANGUAGE=Russian
GEMINI_MODEL=gemini-1.5-flash
ENABLE_STREAMING=true
MAX_RETRIES=3
TRANSLATION_DELAY_SECONDS=0.5
PDF_OUTPUT_DIR=./outputs
LOG_LEVEL=INFO
```

### Available Models

- **Google Gemini**: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-pro`
- **Planned**: OpenAI GPT-4/3.5, Anthropic Claude 3, DeepL (token counting available)

## Development

### Running the App

```bash
streamlit run app.py
```

This will:
1. Start the Streamlit development server
2. Open the app in your web browser
3. Hot-reload on code changes

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python test_translation.py

# Test API key
python test_api_key.py

# Test PDF generation
python test_pdf_generator.py
```

### Code Quality

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

## Advanced Features

### Progress Persistence
- Translations are saved automatically after each paragraph
- Resume interrupted translations from where you left off
- SQLite-based storage for thread-safe concurrent access

### Unicode PDF Generation
- Full Cyrillic (Russian) character support
- Automatic font fallback system
- Professional formatting with preserved structure

### Real-time Streaming
- Watch translations appear live as they're generated
- Character-by-character progress tracking
- Estimated time remaining (ETA) calculations

## License

MIT
