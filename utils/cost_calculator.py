"""
Cost estimation utilities for different LLM providers.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# Pricing per 1M tokens (as of 2024)
PRICING = {
    "openai_gpt4": {
        "provider": "OpenAI",
        "model": "GPT-4 Turbo",
        "input_per_1m": 10.0,  # $10 per 1M input tokens
        "output_per_1m": 30.0,  # $30 per 1M output tokens
    },
    "openai_gpt35": {
        "provider": "OpenAI",
        "model": "GPT-3.5 Turbo",
        "input_per_1m": 0.50,  # $0.50 per 1M input tokens
        "output_per_1m": 1.50,  # $1.50 per 1M output tokens
    },
    "openai_gpt5": {
        "provider": "OpenAI",
        "model": "GPT-5",
        "input_per_1m": 15.0,  # Estimated $15 per 1M input tokens (placeholder pricing)
        "output_per_1m": 45.0,  # Estimated $45 per 1M output tokens (placeholder pricing)
        "note": "Estimated pricing - actual pricing TBD when GPT-5 is released"
    },
    "anthropic_opus": {
        "provider": "Anthropic",
        "model": "Claude 3 Opus",
        "input_per_1m": 15.0,  # $15 per 1M input tokens
        "output_per_1m": 75.0,  # $75 per 1M output tokens
    },
    "anthropic_sonnet": {
        "provider": "Anthropic",
        "model": "Claude 3 Sonnet",
        "input_per_1m": 3.0,  # $3 per 1M input tokens
        "output_per_1m": 15.0,  # $15 per 1M output tokens
    },
    "google_gemini": {
        "provider": "Google",
        "model": "Gemini Pro",
        "input_per_1m": 0.50,  # $0.50 per 1M input tokens
        "output_per_1m": 1.50,  # $1.50 per 1M output tokens
    },
    "google_gemini_3": {
        "provider": "Google",
        "model": "Gemini 3",
        "input_per_1m": 2.0,  # $2.00 per 1M input tokens (for contexts up to 200k tokens)
        "output_per_1m": 12.0,  # $12.00 per 1M output tokens
    },
    "google_gemini_3_flash": {
        "provider": "Google",
        "model": "Gemini 3 Flash",
        "input_per_1m": 0.50,  # Estimated $0.50 per 1M input tokens (placeholder - model not yet released)
        "output_per_1m": 3.0,  # Estimated $3.00 per 1M output tokens (placeholder - model not yet released)
        "note": "Estimated pricing - Gemini 3 Flash not yet released"
    },
    "google_gemini_25_flash": {
        "provider": "Google",
        "model": "Gemini 2.5 Flash",
        "input_per_1m": 0.30,  # $0.30 per 1M input tokens
        "output_per_1m": 2.50,  # $2.50 per 1M output tokens
    },
    "deepl": {
        "provider": "DeepL",
        "model": "DeepL API",
        "input_per_1m": 20.0,  # Approx $20 per 1M characters (DeepL uses character-based pricing)
        "output_per_1m": 0.0,  # DeepL charges only for input
    },
}


def estimate_output_tokens(input_tokens: int, output_ratio: float = 1.3) -> int:
    """
    Estimate output tokens based on input tokens.
    For translation, output is typically 1.2-1.5x the input.
    
    Args:
        input_tokens: Number of input tokens
        output_ratio: Ratio of output to input (default 1.3 for translation)
        
    Returns:
        Estimated output token count
    """
    return int(input_tokens * output_ratio)


def calculate_costs(input_tokens: int, provider_key: str, output_ratio: float = 1.3) -> Dict:
    """
    Calculate cost estimates for a given provider and token count.
    
    Args:
        input_tokens: Number of input tokens
        provider_key: Provider key (e.g., 'openai_gpt4')
        output_ratio: Ratio of output to input tokens (default 1.3)
        
    Returns:
        Dictionary with cost breakdown:
        {
            "provider": "OpenAI",
            "model": "GPT-4 Turbo",
            "input_tokens": 1000,
            "output_tokens": 1300,
            "input_cost": 0.01,
            "output_cost": 0.039,
            "total_cost": 0.049
        }
    """
    logger.debug(f"Calculating costs for {provider_key}: {input_tokens} input tokens, ratio={output_ratio}")
    
    if provider_key not in PRICING:
        logger.error(f"Unknown provider key: {provider_key}")
        raise ValueError(f"Unknown provider key: {provider_key}")
    
    pricing = PRICING[provider_key]
    output_tokens = estimate_output_tokens(input_tokens, output_ratio)
    
    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    total_cost = input_cost + output_cost
    
    result = {
        "provider": pricing["provider"],
        "model": pricing["model"],
        "provider_key": provider_key,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }
    
    # Pass through note if present
    if "note" in pricing:
        result["note"] = pricing["note"]
    
    logger.debug(f"Cost calculation result for {provider_key}: ${total_cost:.4f} total (input: ${input_cost:.4f}, output: ${output_cost:.4f})")
    return result


def calculate_all_provider_costs(token_counts: Dict[str, Dict[str, any]]) -> list:
    """
    Calculate costs for all providers based on their token counts.
    Skips providers with errors or zero tokens.
    
    Args:
        token_counts: Dictionary from calculate_all_provider_tokens()
        
    Returns:
        List of cost dictionaries, sorted by total cost
    """
    logger.debug(f"Calculating costs for {len(token_counts)} providers")
    costs = []
    skipped = 0
    
    for provider_key, token_data in token_counts.items():
        # Skip if there's an error or no tokens
        if "error" in token_data or token_data.get("tokens", 0) == 0:
            skipped += 1
            if "error" in token_data:
                logger.debug(f"Skipping {provider_key} due to error: {token_data['error']}")
            else:
                logger.debug(f"Skipping {provider_key} - zero tokens")
            continue
            
        input_tokens = token_data["tokens"]
        cost_data = calculate_costs(input_tokens, provider_key)
        
        # Add exact/approximate flag
        cost_data["exact"] = token_data.get("exact", False)
        if "note" in token_data:
            cost_data["note"] = token_data["note"]
        
        costs.append(cost_data)
    
    # Sort by total cost (cheapest first)
    costs.sort(key=lambda x: x["total_cost"])
    
    logger.info(f"Cost calculation completed: {len(costs)} providers calculated, {skipped} skipped")
    if costs:
        logger.info(f"Cheapest option: {costs[0]['provider']} {costs[0]['model']} at ${costs[0]['total_cost']:.4f}")
        logger.info(f"Most expensive: {costs[-1]['provider']} {costs[-1]['model']} at ${costs[-1]['total_cost']:.4f}")
    
    return costs

