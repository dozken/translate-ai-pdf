"""
Constants and configuration values for LLM Translation Cost Calculator.
"""
# Streamlit page configuration
PAGE_LAYOUT: str = "wide"

# Default output token ratio for translation (output tokens / input tokens)
DEFAULT_OUTPUT_RATIO: float = 1.3

# Minimum paragraph length for translation (characters)
MIN_PARAGRAPH_LENGTH: int = 10

# Provider Keys (used throughout the application)
PROVIDER_KEYS = {
    "OPENAI_GPT4": "openai_gpt4",
    "OPENAI_GPT35": "openai_gpt35",
    "OPENAI_GPT5": "openai_gpt5",
    "ANTHROPIC_OPUS": "anthropic_opus",
    "ANTHROPIC_SONNET": "anthropic_sonnet",
    "GOOGLE_GEMINI": "google_gemini",
    "DEEPL": "deepl",
}


