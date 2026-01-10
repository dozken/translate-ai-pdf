# PDF Translation Cost Calculator

A Streamlit web application that helps you calculate translation costs for Arabic PDF books to Russian across multiple LLM providers before committing to translation.

## Features

- 📄 **Single PDF Upload**: Upload one PDF file at a time
- 📊 **Free Token Counting**: Calculate token counts using free local methods (no API calls, no credits required)
  - OpenAI: Uses `tiktoken` (exact, free)
  - Anthropic: Uses `tiktoken` approximation (free, close to exact)
  - Google: Uses `tiktoken` approximation (free, close to exact)
  - DeepL: Character count (exact, free, DeepL uses character-based pricing)
- 💰 **Cost Comparison**: See cost estimates side-by-side for all providers
- 🌐 **Translation**: Translate Arabic PDFs to Russian using Google Gemini 3 Pro (paragraph by paragraph)
- 📄 **PDF Output**: Download translated documents as PDF files
- ✅ **Free Token Counting**: All token calculations happen locally - no API costs until you translate

## Quick Start (Using Makefile - Recommended)

The easiest way to get started is using the provided Makefile:

1. **Set up the environment** (creates virtual environment and installs dependencies):
   ```bash
   make setup-env
   ```

2. **Edit `.env` file** with your API keys (it will be created automatically if `.env.example` exists)

3. **Run the application**:
   ```bash
   make run-venv
   ```

4. **View all available commands**:
   ```bash
   make help
   ```

## Installation (Manual)

1. Clone or navigate to this repository:
```bash
cd LLMTranslate
```

2. Install dependencies:
```bash
pip install -e .
```

Or install with development dependencies:
```bash
pip install -e ".[dev]"
```

## Usage

1. Set up configuration:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and configure:
     - **API Keys**: Add your Anthropic and Google API keys
     - **Translation Settings**: Source/target languages (default: Arabic → Russian)
     - **Gemini Model**: Set `GEMINI_MODEL` (default: `gemini-3-pro`). Available models: `gemini-3-pro`, `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`
     - **Performance**: Adjust delay and retry settings if needed
     - **PDF Output**: Optionally set a custom output directory
   - The `.env` file is gitignored and won't be committed

2. Run the Streamlit app:
```bash
streamlit run app.py
```

Or using Makefile:
```bash
make run
```

3. Open your browser to the URL shown (typically `http://localhost:8501`)

4. Upload an Arabic PDF book using the file uploader

5. View:
   - PDF statistics (pages, characters, words)
   - Token counts for each provider (exact or approximate)
   - Cost comparison table
   - Translation buttons (Gemini 3 Pro is fully implemented)

6. Translate:
   - Click "Translate with Gemini" button
   - Confirm translation and estimated cost
   - Watch progress as paragraphs are translated
   - Download the translated PDF file

## Supported LLM Providers

- **OpenAI**: GPT-5, GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet
- **Google**: Gemini 3 Pro (default), Gemini 2.5 Pro/Flash, Gemini 1.5 Pro/Flash
- **DeepL**: DeepL API

**Note**: GPT-5 pricing is estimated (placeholder) until the model is officially released.

## Project Structure

```
LLMTranslate/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration management
├── constants.py           # Constants and messages
├── Makefile              # Makefile for common tasks
├── pyproject.toml        # Modern Python packaging configuration
├── test_translation.py   # Translation test script
├── utils/
│   ├── __init__.py
│   ├── pdf_processor.py   # PDF text extraction
│   ├── token_calculator.py # Token counting for all providers
│   ├── cost_calculator.py  # Cost estimation logic
│   ├── translator.py       # Translation functionality (Gemini 3 Pro)
│   └── pdf_generator.py    # PDF generation from translated text
└── README.md             # This file
```

## How It Works

1. **PDF Processing**: Extracts text from uploaded PDF using `pdfplumber`
2. **Token Counting**: Calculates tokens using free local methods (no API calls):
   - **OpenAI**: Uses `tiktoken` for exact counts (100% free, local)
   - **Anthropic**: Uses `tiktoken` approximation (100% free, local, close to exact)
   - **Google**: Uses `tiktoken` approximation (100% free, local, close to exact)
   - **DeepL**: Returns character count (exact, 100% free, local)
3. **Cost Estimation**: Estimates costs based on current pricing and expected output token ratios
4. **Display**: Shows all results in an easy-to-compare format with indicators for exact vs approximate counts

## Translation Features

- **Gemini 3 Pro Translation**: Fully implemented and ready to use (default model: `gemini-3-pro`)
- **Paragraph-by-Paragraph**: Translates text in manageable chunks for better quality
- **Progress Tracking**: Real-time progress indicator during translation
- **PDF Output**: Generates formatted PDF files with translated content
- **Error Handling**: Comprehensive error handling for API issues, rate limits, and network problems

## Notes

- Token counting is **100% free** - all calculations happen locally, no API calls or credits required
- **OpenAI and DeepL**: Exact token counts using free local methods
- **Anthropic and Google**: Close approximations using free local methods (typically within 5-10% of exact)
- Cost estimates are based on current pricing (as of 2024) and may vary
- Output token estimates assume a 1.3x ratio (typical for translation)
- **Translation requires Google API key** - set `GOOGLE_API_KEY` environment variable
- Translation is done paragraph by paragraph to maintain quality and handle long documents
- Other providers (OpenAI, Anthropic, DeepL) translation coming soon

## Requirements

- Python 3.8+
- See `pyproject.toml` for full dependency list

## Testing

Test the translation functionality with a sample paragraph:

**Using Makefile (recommended):**
```bash
make test-translation
```

**Or manually:**
```bash
# Make sure .env file exists with your API keys
python test_translation.py
```

The test will automatically load API keys from the `.env` file.

This will translate a sample paragraph from the Quranic text and generate a test PDF.

## Available Makefile Commands

The project includes a comprehensive Makefile for common tasks:

- `make help` - Show all available commands
- `make setup-env` - Create virtual environment and install dependencies
- `make run` - Run the Streamlit app
- `make run-venv` - Run the Streamlit app using virtual environment
- `make test-translation` - Run translation test script
- `make install` - Install production dependencies
- `make install-dev` - Install development dependencies
- `make format` - Format code with black
- `make lint` - Lint code with ruff
- `make type-check` - Type check with mypy
- `make check` - Run all code quality checks
- `make clean` - Clean up generated files and caches
- `make info` - Show project information

See `make help` for the complete list of commands.

## License

This project is open source and available for personal and commercial use.

