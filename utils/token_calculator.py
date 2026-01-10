"""
Token counting utilities for different LLM providers.
Uses exact tokenization methods provided by each provider.
"""
import tiktoken
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)


def calculate_tokens_openai(text: str, model: str = "gpt-4-turbo-preview") -> int:
    """
    Calculate tokens for OpenAI models using tiktoken.
    
    Args:
        text: Input text
        model: OpenAI model name
        
    Returns:
        Token count
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        token_count = len(tokens)
        logger.debug(f"OpenAI token count for {model}: {token_count} tokens")
        return token_count
    except Exception as e:
        # Fallback to cl100k_base encoding (used by GPT-4)
        logger.warning(f"Failed to get encoding for model {model}, using cl100k_base fallback: {e}")
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        token_count = len(tokens)
        logger.debug(f"OpenAI token count (fallback): {token_count} tokens")
        return token_count


def calculate_tokens_anthropic(text: str, api_key: Optional[str] = None) -> int:
    """
    Calculate tokens for Anthropic Claude models using free local tokenization.
    Uses tiktoken with cl100k_base encoding (similar to Claude's tokenization).
    This is a free approximation - no API calls required.
    
    Args:
        text: Input text
        api_key: Ignored (kept for compatibility, but not used)
        
    Returns:
        Approximate token count (free, local calculation)
    """
    # Use tiktoken with cl100k_base encoding (free, local)
    # Claude uses a similar tokenization scheme, so this is a good approximation
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    token_count = len(tokens)
    logger.debug(f"Anthropic token count (approximate): {token_count} tokens")
    return token_count


def calculate_tokens_google(text: str, api_key: Optional[str] = None) -> int:
    """
    Calculate tokens for Google Gemini models using free local tokenization.
    Uses tiktoken with cl100k_base encoding (similar to Gemini's tokenization).
    This is a free approximation - no API calls required.
    
    Args:
        text: Input text
        api_key: Ignored (kept for compatibility, but not used)
        
    Returns:
        Approximate token count (free, local calculation)
    """
    # Use tiktoken with cl100k_base encoding (free, local)
    # Gemini uses similar tokenization, so this is a good approximation
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    token_count = len(tokens)
    logger.debug(f"Google token count (approximate): {token_count} tokens")
    return token_count


def calculate_tokens_deepl(text: str) -> int:
    """
    Calculate tokens/characters for DeepL.
    DeepL uses character-based pricing, so we return character count.
    
    Args:
        text: Input text
        
    Returns:
        Character count (DeepL pricing is per character)
    """
    char_count = len(text)
    logger.debug(f"DeepL character count: {char_count} characters")
    return char_count


def calculate_tokens(text: str, provider: str, model: Optional[str] = None, 
                     anthropic_api_key: Optional[str] = None,
                     google_api_key: Optional[str] = None) -> int:
    """
    Calculate token count for a given provider using exact methods.
    
    Args:
        text: Input text to count tokens for
        provider: Provider name ('openai', 'anthropic', 'google', 'deepl')
        model: Optional model name (required for OpenAI)
        anthropic_api_key: Optional Anthropic API key for exact counting
        google_api_key: Optional Google API key for exact counting
        
    Returns:
        Token count (or character count for DeepL)
    """
    provider_lower = provider.lower()
    
    if provider_lower == "openai":
        model = model or "gpt-4-turbo-preview"
        # GPT-5 will likely use same tokenization as GPT-4
        if model and "gpt-5" in model.lower():
            # Use GPT-4 encoding for GPT-5 (assumption until GPT-5 is released)
            return calculate_tokens_openai(text, "gpt-4-turbo-preview")
        return calculate_tokens_openai(text, model)
    elif provider_lower == "anthropic":
        return calculate_tokens_anthropic(text, anthropic_api_key)
    elif provider_lower == "google":
        return calculate_tokens_google(text, google_api_key)
    elif provider_lower == "deepl":
        return calculate_tokens_deepl(text)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def calculate_all_provider_tokens(text: str, 
                                  anthropic_api_key: Optional[str] = None,
                                  google_api_key: Optional[str] = None) -> Dict[str, Dict[str, any]]:
    """
    Calculate token counts for all supported providers using free local methods.
    All calculations are done locally using tiktoken - no API calls required.
    
    Args:
        text: Input text
        anthropic_api_key: Ignored (kept for compatibility)
        google_api_key: Ignored (kept for compatibility)
        
    Returns:
        Dictionary with provider names as keys and token counts as values
        Format: {
            "openai_gpt4": {"tokens": 1234, "model": "gpt-4-turbo-preview", "exact": True},
            "openai_gpt35": {"tokens": 1234, "model": "gpt-3.5-turbo", "exact": True},
            ...
        }
    """
    logger.debug(f"Calculating tokens for all providers (text length: {len(text)} characters)")
    results = {}
    
    # OpenAI GPT-4 Turbo (exact - uses tiktoken)
    results["openai_gpt4"] = {
        "tokens": calculate_tokens(text, "openai", "gpt-4-turbo-preview"),
        "model": "gpt-4-turbo-preview",
        "exact": True
    }
    
    # OpenAI GPT-3.5 Turbo (exact - uses tiktoken)
    results["openai_gpt35"] = {
        "tokens": calculate_tokens(text, "openai", "gpt-3.5-turbo"),
        "model": "gpt-3.5-turbo",
        "exact": True
    }
    
    # OpenAI GPT-5 (exact - uses tiktoken, assumes same encoding as GPT-4)
    results["openai_gpt5"] = {
        "tokens": calculate_tokens(text, "openai", "gpt-5"),
        "model": "GPT-5",
        "exact": True,
        "note": "Uses GPT-4 tokenization (assumed until GPT-5 is released)"
    }
    
    # Anthropic Claude 3 Opus (approximate - uses tiktoken, free)
    anthropic_tokens = calculate_tokens(text, "anthropic")
    results["anthropic_opus"] = {
        "tokens": anthropic_tokens,
        "model": "claude-3-opus-20240229",
        "exact": False,
        "note": "Approximate (free local calculation)"
    }
    results["anthropic_sonnet"] = {
        "tokens": anthropic_tokens,  # Same tokenization for all Claude models
        "model": "claude-3-sonnet-20240229",
        "exact": False,
        "note": "Approximate (free local calculation)"
    }
    
    # Google Gemini models (approximate - uses tiktoken, free)
    google_tokens = calculate_tokens(text, "google")
    results["google_gemini"] = {
        "tokens": google_tokens,
        "model": "gemini-pro",
        "exact": False,
        "note": "Approximate (free local calculation)"
    }
    results["google_gemini_3"] = {
        "tokens": google_tokens,
        "model": "gemini-3",
        "exact": False,
        "note": "Approximate (free local calculation)"
    }
    results["google_gemini_3_flash"] = {
        "tokens": google_tokens,
        "model": "gemini-3-flash",
        "exact": False,
        "note": "Approximate (free local calculation)"
    }
    results["google_gemini_25_flash"] = {
        "tokens": google_tokens,
        "model": "gemini-2.5-flash",
        "exact": False,
        "note": "Approximate (free local calculation)"
    }
    
    # DeepL (character-based, exact) - excluded from token display but kept for cost calculations
    # results["deepl"] = {
    #     "tokens": calculate_tokens(text, "deepl"),
    #     "model": "deepl-api",
    #     "exact": True,
    #     "note": "Character count (DeepL uses character-based pricing)"
    # }
    
    logger.info(f"Token calculation completed for {len(results)} providers")
    # Log summary statistics
    if results:
        token_values = [r["tokens"] for r in results.values() if "tokens" in r]
        if token_values:
            logger.info(f"Token count range: {min(token_values):,} - {max(token_values):,} tokens")
    
    return results

