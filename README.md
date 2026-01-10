# LLM Translate - Tauri Desktop App

PDF Translation Cost Calculator - Native desktop application built with Tauri and Rust.

## Features

- 📄 **PDF Processing**: Extract text from PDF files
- 📊 **Token Counting**: Calculate token counts for all major LLM providers (free, local)
- 💰 **Cost Comparison**: Compare translation costs across providers
- 🌐 **Translation**: Translate Arabic PDFs to Russian using Google Gemini
- 📄 **PDF Output**: Generate translated PDFs with proper formatting
- 💾 **Progress Saving**: Resume interrupted translations
- 🚀 **Native Performance**: Fast, responsive desktop application

## Architecture

- **Frontend**: Vanilla HTML/JavaScript
- **Backend**: Rust (Tauri)
- **PDF Processing**: pdf-extract crate
- **Token Counting**: tiktoken-rs
- **Translation API**: Google Gemini (via reqwest)
- **PDF Generation**: printpdf

## Prerequisites

- Rust (latest stable) - Install from https://rustup.rs/
- Node.js (v18+) - Install from https://nodejs.org/
- Tauri CLI will be installed via npm dependencies

## Setup

1. **Install dependencies:**
   ```bash
   cd app-tauri
   npm install
   cd src-tauri
   cargo build  # This will download Rust dependencies
   ```

2. **Configure environment:**
   ```bash
   cd ../..  # Back to root
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

3. **Run in development:**
   ```bash
   cd app-tauri
   npm run dev
   ```

4. **Build for production:**
   ```bash
   cd app-tauri
   npm run build
   ```

## Project Structure

```
LLMTranslate/
├── app-tauri/             # Tauri desktop application
│   ├── src/               # Frontend (vanilla HTML/JS)
│   │   ├── index.html
│   │   ├── main.js
│   │   └── styles.css
│   ├── src-tauri/         # Rust backend
│   │   ├── src/
│   │   │   ├── main.rs
│   │   │   ├── commands/  # Tauri IPC commands
│   │   │   ├── services/  # Business logic
│   │   │   ├── config.rs
│   │   │   ├── models.rs
│   │   │   └── error.rs
│   │   └── Cargo.toml
│   └── package.json
├── python-streamlit/      # Original Streamlit implementation
└── README.md
```

## Usage

1. Launch the application
2. Upload a PDF file
3. View token counts and cost estimates
4. Select a provider (currently Google Gemini)
5. Start translation
6. Download the translated PDF

## Configuration

Create a `.env` file in the project root (same level as `app-tauri/`):

```env
GOOGLE_API_KEY=your_api_key_here
SOURCE_LANGUAGE=Arabic
TARGET_LANGUAGE=Russian
GEMINI_MODEL=gemini-3-pro
ENABLE_STREAMING=true
MAX_RETRIES=3
TRANSLATION_DELAY_SECONDS=0.5
```

## Development

The app uses Tauri's IPC system for communication between frontend and backend:

- Frontend calls: `invoke('command_name', { args })`
- Backend commands: Defined in `app-tauri/src-tauri/src/commands/`

### Running the App

From the `app-tauri/` directory:

```bash
cd app-tauri
npm run dev
```

This will:
1. Start the Tauri development server
2. Open a native window with your app
3. Hot-reload on code changes

## Building

Build for your platform:

```bash
cd app-tauri
npm run build
```

Outputs will be in `app-tauri/src-tauri/target/release/`

## License

MIT
