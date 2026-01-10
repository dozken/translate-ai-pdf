"""
Utils package for LLM Translation Cost Calculator.

This package provides utilities for:
- PDF processing and text extraction
- Token counting for various LLM providers
- Cost calculation and estimation
- Text translation using LLM APIs
- PDF generation from translated text
"""

__version__ = "0.1.0"

# Import commonly used functions for easier access
from utils.pdf_processor import extract_text_from_pdf
from utils.token_calculator import calculate_all_provider_tokens, calculate_tokens
from utils.cost_calculator import calculate_all_provider_costs, calculate_costs
from utils.translator import translate_text_gemini, split_into_paragraphs
from utils.pdf_generator import create_pdf_from_text

__all__ = [
    "extract_text_from_pdf",
    "calculate_all_provider_tokens",
    "calculate_tokens",
    "calculate_all_provider_costs",
    "calculate_costs",
    "translate_text_gemini",
    "split_into_paragraphs",
    "create_pdf_from_text",
]


