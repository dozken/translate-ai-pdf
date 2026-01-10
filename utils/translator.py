"""
Translation utilities for translating text using various LLM providers.
"""
import time
import logging
import re
import concurrent.futures
import threading
from typing import List, Optional, Callable, Dict

logger = logging.getLogger(__name__)


def calculate_paragraph_metrics(paragraphs: List[str]) -> Dict:
    """
    Calculate quality metrics for paragraph splitting.
    
    Phase 1: Monitoring function to track paragraph splitting quality.
    Helps identify over-segmentation and under-segmentation issues.
    
    Args:
        paragraphs: List of paragraph strings
        
    Returns:
        Dictionary with metrics:
        - count: Number of paragraphs
        - avg_size: Average paragraph size in characters
        - min_size: Minimum paragraph size
        - max_size: Maximum paragraph size
        - over_segmented: Count of paragraphs < 100 chars
        - under_segmented: Count of paragraphs > 2000 chars
        - over_segmented_rate: Percentage of over-segmented paragraphs
        - under_segmented_rate: Percentage of under-segmented paragraphs
        - size_distribution: Distribution across size buckets
        - medium_range_percentage: Percentage in ideal range (500-1500 chars)
    """
    if not paragraphs:
        return {
            'count': 0,
            'avg_size': 0,
            'min_size': 0,
            'max_size': 0,
            'over_segmented': 0,
            'under_segmented': 0,
            'over_segmented_rate': 0.0,
            'under_segmented_rate': 0.0,
            'size_distribution': {
                'tiny (< 100)': 0,
                'small (100-500)': 0,
                'medium (500-1500)': 0,
                'large (1500-2000)': 0,
                'huge (> 2000)': 0,
            },
            'medium_range_percentage': 0.0
        }
    
    sizes = [len(p) for p in paragraphs]
    count = len(paragraphs)
    avg_size = sum(sizes) / count if count > 0 else 0
    min_size = min(sizes) if sizes else 0
    max_size = max(sizes) if sizes else 0
    
    # Count over-segmented (< 100 chars) and under-segmented (> 2000 chars)
    over_segmented = sum(1 for s in sizes if s < 100)
    under_segmented = sum(1 for s in sizes if s > 2000)
    
    # Size distribution buckets (Phase 1 targets: 60-70% in medium range)
    distribution = {
        'tiny (< 100)': sum(1 for s in sizes if s < 100),
        'small (100-500)': sum(1 for s in sizes if 100 <= s < 500),
        'medium (500-1500)': sum(1 for s in sizes if 500 <= s < 1500),
        'large (1500-2000)': sum(1 for s in sizes if 1500 <= s <= 2000),
        'huge (> 2000)': sum(1 for s in sizes if s > 2000),
    }
    
    medium_range_count = distribution['medium (500-1500)']
    medium_range_percentage = (medium_range_count / count * 100) if count > 0 else 0.0
    
    return {
        'count': count,
        'avg_size': round(avg_size, 1),
        'min_size': min_size,
        'max_size': max_size,
        'over_segmented': over_segmented,
        'under_segmented': under_segmented,
        'over_segmented_rate': round(over_segmented / count * 100, 1) if count > 0 else 0.0,
        'under_segmented_rate': round(under_segmented / count * 100, 1) if count > 0 else 0.0,
        'size_distribution': distribution,
        'medium_range_percentage': round(medium_range_percentage, 1)
    }


def _group_consecutive_verses(paragraphs: List[str], min_length: int = 50) -> List[str]:
    """
    Group consecutive verse-numbered paragraphs together.
    
    Phase 1 improvement: Prevents over-segmentation by grouping verses
    that should stay together (e.g., "1. text", "2. text", "3. text").
    
    Args:
        paragraphs: List of paragraph strings
        min_length: Minimum length for a paragraph
        
    Returns:
        List of paragraphs with verses grouped
    """
    if not paragraphs:
        return []
    
    # Pattern to detect verse numbers at start of line (e.g., "1. ", "2) ", "١. ")
    verse_pattern = re.compile(r'^[\d\u0660-\u0669]+[\.\)]\s+')
    
    grouped = []
    current_verse_group = []
    
    for para in paragraphs:
        para_stripped = para.strip()
        
        # Check if this paragraph looks like a verse
        if verse_pattern.match(para_stripped):
            # This is a verse, add to current group
            current_verse_group.append(para_stripped)
        else:
            # Not a verse - finalize current verse group if any
            if current_verse_group:
                # Group verses together, but respect max size limits
                grouped_text = " ".join(current_verse_group)
                if len(grouped_text) >= min_length:
                    grouped.append(grouped_text)
                current_verse_group = []
            
            # Add non-verse paragraph
            if len(para_stripped) >= min_length:
                grouped.append(para_stripped)
    
    # Add any remaining verse group
    if current_verse_group:
        grouped_text = " ".join(current_verse_group)
        if len(grouped_text) >= min_length:
            grouped.append(grouped_text)
    
    return grouped if grouped else paragraphs


def split_into_paragraphs(text: str, min_length: int = 50, max_paragraph_size: int = 2000) -> List[str]:
    """
    Split text into paragraphs, preserving structure.
    Handles PDF text that may not have proper paragraph breaks.
    
    Phase 1 improvements:
    - Increased substantial threshold from 300 to 800 chars
    - Tighter pattern matching to reduce over-segmentation
    - Verse grouping to prevent splitting on verse numbers
    - Better size management (target 70-80% of max)
    
    Args:
        text: Input text to split
        min_length: Minimum paragraph length to include (skip very short paragraphs)
        max_paragraph_size: Maximum size for a paragraph before splitting (default: 2000 chars)
        
    Returns:
        List of paragraphs
    """
    if not text or not text.strip():
        return []
    
    # Normalize whitespace: collapse multiple spaces and normalize newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)  # Collapse 3+ newlines to 2
    
    # Strategy 1: Split on double newlines (clear paragraph breaks)
    paragraphs = text.split('\n\n')
    
    # Clean and filter paragraphs
    cleaned_paragraphs = []
    for para in paragraphs:
        # Strip whitespace and normalize internal newlines
        para = para.strip()
        para = re.sub(r'\s+', ' ', para)  # Replace all whitespace with single space
        
        # Skip empty or very short paragraphs
        if len(para) >= min_length:
            cleaned_paragraphs.append(para)
    
    # Phase 1: Group consecutive verses together before further processing
    if len(cleaned_paragraphs) > 1:
        cleaned_paragraphs = _group_consecutive_verses(cleaned_paragraphs, min_length)
    
    # If we got multiple reasonable paragraphs, merge very short ones aggressively
    if len(cleaned_paragraphs) > 1:
        # More aggressive merging: merge short paragraphs up to 70% of max size
        merged_paragraphs = []
        merge_threshold = max_paragraph_size * 0.7  # Target 70% of max for merging
        
        for para in cleaned_paragraphs:
            # If current paragraph is short and previous exists, try to merge
            if len(para) < min_length * 3 and merged_paragraphs:
                potential_merge = merged_paragraphs[-1] + " " + para
                # Only merge if result is still under threshold
                if len(potential_merge) <= merge_threshold:
                    merged_paragraphs[-1] = potential_merge
                else:
                    merged_paragraphs.append(para)
            else:
                merged_paragraphs.append(para)
        cleaned_paragraphs = merged_paragraphs
    
    # If we only got 1 paragraph and it's very large, use fallback strategies
    if len(cleaned_paragraphs) == 1 and len(cleaned_paragraphs[0]) > max_paragraph_size:
        logger.info(f"Large single paragraph detected ({len(cleaned_paragraphs[0])} chars), using fallback splitting strategies")
        large_text = cleaned_paragraphs[0]
        cleaned_paragraphs = []
        
        # Strategy 2: Try splitting on single newlines, but only where there are clear breaks
        # Look for patterns that indicate paragraph boundaries
        lines = text.split('\n')
        potential_paragraphs = []
        current_para = []
        consecutive_empty = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                consecutive_empty += 1
                # If we have 2+ empty lines, that's a clear paragraph break
                if consecutive_empty >= 2 and current_para:
                    para_text = ' '.join(current_para).strip()
                    para_text = re.sub(r'\s+', ' ', para_text)
                    if len(para_text) >= min_length:
                        potential_paragraphs.append(para_text)
                    current_para = []
                continue
            
            consecutive_empty = 0
            
            # Check if this line looks like the start of a new paragraph
            # Only split if we have a substantial current paragraph AND clear indicators
            should_start_new = False
            if current_para:
                prev_text = ' '.join(current_para[-2:]) if len(current_para) >= 2 else current_para[-1]
                
                # Strong indicators of paragraph break (Phase 1 improvements):
                # 1. Previous line ends with sentence punctuation AND this line starts with capital/arabic
                # 2. This line starts with common paragraph markers (but not just any number)
                # 3. Current paragraph is already substantial (>= 800 chars) - increased from 300
                # 4. Require multiple indicators to avoid over-segmentation
                
                current_para_text = ' '.join(current_para)
                current_para_size = len(current_para_text)
                
                # Check for sentence-ending punctuation (including Arabic punctuation)
                ends_with_punctuation = bool(re.search(r'[.!?؟]\s*$', prev_text))
                
                # Tighter pattern matching - don't split on every number/Arabic char
                # Only match clear paragraph markers: capital letters, verse numbers with punctuation, or clear Arabic starts
                # Verse pattern: number followed by period/paren and space (e.g., "1. ", "2) ")
                verse_pattern = re.match(r'^\d+[\.\)]\s+', line_stripped)
                starts_with_capital = bool(re.match(r'^[A-ZА-Я\u0600-\u06FF]', line_stripped))
                starts_with_clear_marker = verse_pattern or starts_with_capital
                
                # Require substantial paragraph (800 chars minimum, up from 300)
                is_substantial = current_para_size >= 800
                
                # Only split if we have MULTIPLE strong indicators AND current para is substantial
                # This prevents over-segmentation on verse numbers alone
                has_multiple_indicators = ends_with_punctuation and starts_with_clear_marker
                
                if has_multiple_indicators and is_substantial:
                    should_start_new = True
                # Or if current paragraph is getting too large (target 70-80% of max)
                elif current_para_size >= max_paragraph_size * 0.75:
                    should_start_new = True
            
            if should_start_new and current_para:
                para_text = ' '.join(current_para).strip()
                para_text = re.sub(r'\s+', ' ', para_text)
                if len(para_text) >= min_length:
                    potential_paragraphs.append(para_text)
                current_para = [line_stripped]
            else:
                current_para.append(line_stripped)
        
        # Add the last paragraph
        if current_para:
            para_text = ' '.join(current_para).strip()
            para_text = re.sub(r'\s+', ' ', para_text)
            if len(para_text) >= min_length:
                potential_paragraphs.append(para_text)
        
        if len(potential_paragraphs) > 1:
            logger.debug(f"Found {len(potential_paragraphs)} paragraphs using line-based splitting")
            cleaned_paragraphs = potential_paragraphs
        else:
            # Strategy 3: Split by sentence boundaries, grouping sentences intelligently
            # Use a more robust sentence pattern that handles multiple languages
            sentence_pattern = r'([.!?])\s+'
            parts = re.split(sentence_pattern, large_text)
            
            # Reconstruct sentences
            sentences = []
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    sentence = parts[i] + parts[i + 1]
                else:
                    sentence = parts[i] if i < len(parts) else ""
                sentence = sentence.strip()
                if sentence and len(sentence) >= 10:  # Skip very short fragments
                    sentences.append(sentence)
            
            # Group sentences into paragraphs intelligently
            if sentences:
                logger.debug(f"Found {len(sentences)} sentences, grouping into paragraphs")
                current_para = ""
                target_size = max_paragraph_size * 0.75  # Phase 1: Target 75% of max (70-80% range)
                substantial_threshold = 800  # Phase 1: Require substantial paragraphs before splitting
                
                for sentence in sentences:
                    potential_para = current_para + " " + sentence if current_para else sentence
                    
                    # Phase 1: Only split if current para is substantial AND would exceed target
                    # This prevents over-segmentation of small paragraphs
                    if (current_para and 
                        len(current_para) >= substantial_threshold and 
                        len(potential_para) > target_size):
                        if len(current_para) >= min_length:
                            cleaned_paragraphs.append(current_para)
                        current_para = sentence
                    else:
                        current_para = potential_para
                    
                    # If current paragraph exceeds max size, force split
                    if len(current_para) > max_paragraph_size:
                        # Split at the last sentence boundary
                        if len(cleaned_paragraphs) > 0 or len(current_para) > min_length:
                            # Try to split at a reasonable point
                            words = current_para.split()
                            mid_point = len(words) // 2
                            first_half = ' '.join(words[:mid_point])
                            second_half = ' '.join(words[mid_point:])
                            
                            if len(first_half) >= min_length:
                                cleaned_paragraphs.append(first_half)
                            current_para = second_half
                
                # Add the last paragraph
                if current_para and len(current_para) >= min_length:
                    cleaned_paragraphs.append(current_para)
            
            # Strategy 4: If sentence splitting didn't work well, use word-based chunking
            if len(cleaned_paragraphs) == 0 or (len(cleaned_paragraphs) == 1 and len(cleaned_paragraphs[0]) > max_paragraph_size):
                logger.debug("Using word-based chunking as fallback")
                cleaned_paragraphs = []
                words = large_text.split()
                current_chunk = []
                current_size = 0
                target_chunk_size = max_paragraph_size * 0.8  # Aim for 80% of max
                
                for word in words:
                    word_size = len(word) + 1  # +1 for space
                    if current_size + word_size > target_chunk_size and current_chunk:
                        chunk_text = ' '.join(current_chunk).strip()
                        if len(chunk_text) >= min_length:
                            cleaned_paragraphs.append(chunk_text)
                        current_chunk = [word]
                        current_size = len(word)
                    else:
                        current_chunk.append(word)
                        current_size += word_size
                
                # Add the last chunk
                if current_chunk:
                    chunk_text = ' '.join(current_chunk).strip()
                    if len(chunk_text) >= min_length:
                        cleaned_paragraphs.append(chunk_text)
    
    # Final cleanup: Phase 1 - more aggressive merging of short paragraphs
    final_paragraphs = []
    merge_threshold = max_paragraph_size * 0.75  # Phase 1: Target 75% for merging
    
    for para in cleaned_paragraphs:
        para = re.sub(r'\s+', ' ', para).strip()
        
        # If paragraph is too large, split it
        if len(para) > max_paragraph_size * 1.5:
            # Split very large paragraphs by word count
            words = para.split()
            current_chunk = []
            current_size = 0
            target_size = max_paragraph_size * 0.8  # Phase 1: Target 80% when splitting
            
            for word in words:
                word_size = len(word) + 1
                if current_size + word_size > target_size and current_chunk:
                    chunk_text = ' '.join(current_chunk).strip()
                    if len(chunk_text) >= min_length:
                        final_paragraphs.append(chunk_text)
                    current_chunk = [word]
                    current_size = len(word)
                else:
                    current_chunk.append(word)
                    current_size += word_size
            
            if current_chunk:
                chunk_text = ' '.join(current_chunk).strip()
                if len(chunk_text) >= min_length:
                    final_paragraphs.append(chunk_text)
        elif len(para) >= min_length:
            # Phase 1: More aggressive merging - merge if previous para is under threshold
            # This helps reduce over-segmentation by combining small paragraphs
            if (final_paragraphs and 
                len(final_paragraphs[-1]) < merge_threshold and
                len(para) < min_length * 4):  # Merge paragraphs up to 4x min_length
                potential_merge = final_paragraphs[-1] + " " + para
                # Only merge if result stays under max size
                if len(potential_merge) <= max_paragraph_size:
                    final_paragraphs[-1] = potential_merge
                else:
                    final_paragraphs.append(para)
            else:
                final_paragraphs.append(para)
    
    # Phase 1: Log detailed metrics for monitoring
    if len(final_paragraphs) > 1:
        metrics = calculate_paragraph_metrics(final_paragraphs)
        logger.info(
            f"Split text into {metrics['count']} paragraphs "
            f"(avg {metrics['avg_size']} chars, range: {metrics['min_size']}-{metrics['max_size']})"
        )
        logger.debug(
            f"Paragraph metrics: over-segmented {metrics['over_segmented_rate']}%, "
            f"under-segmented {metrics['under_segmented_rate']}%, "
            f"medium range {metrics['medium_range_percentage']}%"
        )
        
        # Phase 1: Alert on high over-segmentation (> 30% is concerning)
        if metrics['over_segmented_rate'] > 30:
            logger.warning(
                f"High over-segmentation detected: {metrics['over_segmented_rate']}% "
                f"({metrics['over_segmented']}/{metrics['count']} paragraphs < 100 chars). "
                f"Target: < 10%"
            )
    elif len(final_paragraphs) == 1:
        logger.info(f"Text kept as single paragraph ({len(final_paragraphs[0])} chars)")
    
    return final_paragraphs


def translate_paragraph_gemini(
    paragraph: str, 
    api_key: str, 
    max_retries: Optional[int] = None, 
    model_name: Optional[str] = None, 
    source_lang: str = "Arabic", 
    target_lang: str = "Russian",
    stream: bool = False,
    stream_callback: Optional[Callable[[str, str], None]] = None
) -> str:
    """
    Translate a single paragraph using Gemini Pro.
    
    Args:
        paragraph: Text paragraph to translate
        api_key: Google Gemini API key
        max_retries: Maximum number of retry attempts (default: from env or 3)
        model_name: Gemini model name (default: from env or 'gemini-pro')
        source_lang: Source language name (default: from env or 'Arabic')
        target_lang: Target language name (default: from env or 'Russian')
        stream: If True, use streaming mode for real-time updates
        stream_callback: Optional callback function(chunk_text, accumulated_text) called for each chunk
        
    Returns:
        Translated paragraph
        
    Raises:
        ValueError: If API key is invalid or empty
        ImportError: If google-generativeai package is not installed
        Exception: For other API errors (rate limits, network issues, etc.)
    """
    if not api_key or not api_key.strip():
        logger.error("Google API key is required but not provided")
        raise ValueError("Google API key is required but not provided")
    
    # Import config here to avoid circular imports
    from config import config
    
    # Get defaults from config
    if max_retries is None:
        max_retries = config.MAX_RETRIES
    if model_name is None:
        model_name = config.GEMINI_MODEL
    if source_lang == "Arabic":  # Only override if using default
        source_lang = config.SOURCE_LANGUAGE
    if target_lang == "Russian":  # Only override if using default
        target_lang = config.TARGET_LANGUAGE
    
    logger.debug(f"Translating paragraph ({len(paragraph)} chars) using {model_name}: {source_lang} -> {target_lang}")
    
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Generation config for better translation accuracy
        # Temperature=0 for fully deterministic, most accurate translations
        generation_config = genai.GenerationConfig(
            temperature=0.0,  # Zero temperature for fully deterministic, most accurate translations
            top_p=0.95,       # Nucleus sampling for focused responses
            top_k=40,         # Limit vocabulary choices for consistency
        )
        
        # Create translation prompt with improved instructions for accuracy
        prompt = f"""You are an expert translator specializing in accurate, context-aware translations from {source_lang} to {target_lang}. 

Instructions:
- Translate the text with precision, maintaining the exact meaning and nuance
- Preserve the original structure, formatting, and style
- For religious or classical texts, use appropriate terminology and maintain reverence
- Keep all proper nouns, names, and technical terms accurate
- Return ONLY the translation without any explanations, prefixes, or additional commentary

{source_lang} text:
{paragraph}

{target_lang} translation:"""
        
        # Retry logic
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.debug(f"Translation attempt {attempt + 1}/{max_retries} (stream={stream})")
                
                if stream:
                    # Streaming mode
                    response = model.generate_content(
                        prompt, 
                        stream=True,
                        generation_config=generation_config
                    )
                    accumulated = ""
                    
                    try:
                        for chunk in response:
                            try:
                                chunk_text = chunk.text
                            except Exception:
                                # Handle cases where chunk has no text (e.g. safety blockage)
                                logger.debug(f"Skipped chunk with no text (reason: {chunk.candidates[0].finish_reason if chunk.candidates else 'unknown'})")
                                continue
                                
                            if chunk_text:
                                accumulated += chunk_text
                                # Call stream callback with chunk and accumulated text
                                if stream_callback:
                                    try:
                                        stream_callback(chunk_text, accumulated)
                                    except Exception as callback_error:
                                        logger.warning(f"Stream callback error: {callback_error}")
                        
                        if accumulated:
                            translated = accumulated.strip()
                            # Remove any potential prefix/suffix that model might add
                            if translated.startswith(f"{target_lang} translation:"):
                                translated = translated.replace(f"{target_lang} translation:", "").strip()
                            if translated.startswith("Translation:"):
                                translated = translated.replace("Translation:", "").strip()
                            logger.debug(f"Streaming translation successful: {len(translated)} characters")
                            return translated
                        else:
                            logger.warning("Empty response from Gemini API (streaming)")
                            raise ValueError("Empty response from Gemini API")
                    except Exception as stream_error:
                        # If streaming fails, log and fall back to non-streaming
                        logger.warning(f"Streaming failed, falling back to non-streaming: {stream_error}")
                        stream = False
                        # Continue to non-streaming code below
                
                if not stream:
                    # Non-streaming mode (original implementation)
                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )
                    
                    if response and response.text:
                        translated = response.text.strip()
                        # Remove any potential prefix/suffix that model might add
                        if translated.startswith(f"{target_lang} translation:"):
                            translated = translated.replace(f"{target_lang} translation:", "").strip()
                        if translated.startswith("Translation:"):
                            translated = translated.replace("Translation:", "").strip()
                        logger.debug(f"Translation successful: {len(translated)} characters")
                        return translated
                    else:
                        logger.warning("Empty response from Gemini API")
                        raise ValueError("Empty response from Gemini API")
                    
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check for rate limit errors (429)
                if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                    if attempt < max_retries - 1:
                        # Wait longer for rate limits (exponential backoff)
                        wait_time = (2 ** attempt) * 2
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 2}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts: {e}")
                        raise Exception(f"Rate limit exceeded. Please try again later. Error: {str(e)}")
                
                # Check for authentication errors
                elif "401" in error_str or "403" in error_str or "invalid" in error_str or "authentication" in error_str:
                    logger.error(f"Authentication error: {e}")
                    raise ValueError(f"Invalid API key or authentication failed: {str(e)}")
                
                # Check for network errors
                elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Network error, waiting {wait_time}s before retry {attempt + 2}/{max_retries}: {e}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Network error after {max_retries} attempts: {e}")
                        raise Exception(f"Network error. Please check your connection and try again. Error: {str(e)}")
                
                # Other errors
                else:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 0.5
                        logger.warning(f"Translation error, waiting {wait_time}s before retry {attempt + 2}/{max_retries}: {e}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Translation failed after {max_retries} attempts: {e}")
                        raise Exception(f"Translation failed after {max_retries} attempts: {str(e)}")
        
        # If we get here, all retries failed
        logger.error(f"All retry attempts failed. Last error: {last_error}")
        raise Exception(f"Translation failed: {str(last_error)}")
                    
    except ValueError:
        raise  # Re-raise ValueError as-is
    except ImportError as e:
        logger.error(f"Missing required package: {e}")
        raise  # Re-raise ImportError as-is
    except Exception as e:
        # Wrap other exceptions
        logger.error(f"Unexpected error translating paragraph: {e}", exc_info=True)
        raise Exception(f"Error translating paragraph: {str(e)}")


class TranslationStoppedException(Exception):
    """Exception raised when translation is stopped by user."""
    pass


def translate_text_gemini(
    text: str, 
    api_key: str, 
    source_lang: Optional[str] = None, 
    target_lang: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    model_name: Optional[str] = None,
    max_retries: Optional[int] = None,
    delay_seconds: Optional[float] = None,
    stream: bool = False,
    stream_callback: Optional[Callable[[int, str, str], None]] = None,
    progress_file_id: Optional[str] = None,
    resume_from_index: int = 0,
    stop_check: Optional[Callable[[], bool]] = None
) -> str:
    """
    Translate text paragraph by paragraph using Gemini Pro.
    
    Args:
        text: Input text to translate
        api_key: Google Gemini API key
        source_lang: Source language (default: from env or Arabic)
        target_lang: Target language (default: from env or Russian)
        progress_callback: Optional callback function(current, total) for progress updates
        model_name: Gemini model name (default: from env or gemini-pro)
        max_retries: Maximum retry attempts (default: from env or 3)
        delay_seconds: Delay between paragraph translations (default: from env or 0.5)
        stream: If True, use streaming mode for real-time updates
        stream_callback: Optional callback function(paragraph_idx, chunk_text, accumulated_text) for streaming updates
        progress_file_id: Optional file identifier for saving progress (enables resume capability)
        resume_from_index: Index to resume from (0-based, 0 means start from beginning)
        stop_check: Optional callback function() -> bool that returns True if translation should stop
        
    Returns:
        Translated text with preserved paragraph structure
        
    Raises:
        ValueError: If API key is invalid
        TranslationStoppedException: If translation is stopped by user via stop_check
        Exception: For translation errors
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty")
    
    if not api_key or not api_key.strip():
        raise ValueError("Google API key is required but not provided")
    
    # Import config here to avoid circular imports
    from config import config
    
    # Get defaults from config
    if source_lang is None:
        source_lang = config.SOURCE_LANGUAGE
    if target_lang is None:
        target_lang = config.TARGET_LANGUAGE
    if model_name is None:
        model_name = config.GEMINI_MODEL
    if max_retries is None:
        max_retries = config.MAX_RETRIES
    if delay_seconds is None:
        delay_seconds = config.TRANSLATION_DELAY_SECONDS
    
    # Import progress storage here to avoid circular imports
    from utils.progress_storage import (
        load_progress, 
        update_progress_paragraph,
        get_translated_text_from_progress
    )
    
    # Split into paragraphs
    paragraphs = split_into_paragraphs(text)
    logger.info(f"Text split into {len(paragraphs)} paragraphs for translation")
    
    if not paragraphs:
        logger.warning("No paragraphs found in text after splitting")
        return ""
    
    total_paragraphs = len(paragraphs)
    translated_paragraphs = []
    failed_paragraphs = []
    
    # Handle resume logic
    if progress_file_id and resume_from_index > 0:
        # Load existing progress
        existing_progress = load_progress(progress_file_id)
        if existing_progress:
            # Reconstruct already-translated paragraphs
            existing_translated = existing_progress.get('translated_paragraphs', {})
            for idx in range(resume_from_index):
                if str(idx) in existing_translated:
                    translated_paragraphs.append(existing_translated[str(idx)])
                else:
                    # If a paragraph is missing, we'll need to translate it
                    translated_paragraphs.append(None)
            
            logger.info(
                f"Resuming translation from paragraph {resume_from_index + 1}/{total_paragraphs} "
                f"for file_id: {progress_file_id}"
            )
        else:
            logger.warning(
                f"Resume requested but no progress found for file_id: {progress_file_id}, "
                f"starting from beginning"
            )
            resume_from_index = 0
    else:
        resume_from_index = 0
    
    # Initialize translated_paragraphs list with None placeholders for all paragraphs
    # This allows valid index access even if we resume partway through or fill out of order
    if resume_from_index == 0:
        translated_paragraphs = [None] * total_paragraphs
    else:
        # If resuming, we already have some items. Pad the rest with None.
        # Ensure translated_paragraphs has correct length
        if len(translated_paragraphs) < total_paragraphs:
            translated_paragraphs.extend([None] * (total_paragraphs - len(translated_paragraphs)))

    logger.info(f"Starting translation of {total_paragraphs} paragraphs using {model_name} with {config.MAX_WORKERS} workers")
    
    # Thread-safe lock for callbacks and progress updates
    progress_lock = threading.Lock()
    
    def process_paragraph(idx: int):
        """Process a single paragraph inside a thread."""
        # Check stop flag (thread-safe read)
        if stop_check and stop_check():
            return None
            
        paragraph = paragraphs[idx]
        paragraph_num = idx + 1
        
        try:
            # Paragraph-level stream callback
            def paragraph_stream_callback(chunk_text: str, accumulated: str):
                if stream_callback:
                    with progress_lock:
                        # Construct a partial view of the document for the callback
                        # Note: This is an approximation in parallel mode.
                        # We use the current state of translated_paragraphs
                        current_doc = []
                        for i, p in enumerate(translated_paragraphs):
                            if i == idx:
                                current_doc.append(accumulated)
                            elif p is not None:
                                current_doc.append(p)
                                
                        full_accumulated = '\n\n'.join(current_doc)
                        try:
                            stream_callback(paragraph_num, chunk_text, full_accumulated)
                        except Exception as e:
                            logger.error(f"Stream callback error: {e}")

            # Translate
            translation = translate_paragraph_gemini(
                paragraph, 
                api_key, 
                max_retries=max_retries,
                model_name=model_name,
                source_lang=source_lang,
                target_lang=target_lang,
                stream=stream,
                stream_callback=paragraph_stream_callback if stream else None
            )
            
            # Update results safely
            # List reassignment at index is atomic in simple cases, but using lock for clarity/safety with complex objects
            with progress_lock:
                translated_paragraphs[idx] = translation
                
                # Save progress
                if progress_file_id:
                    try:
                        update_progress_paragraph(
                            file_id=progress_file_id,
                            paragraph_idx=idx,
                            translated_text=translation,
                            original_paragraphs=paragraphs,
                            source_lang=source_lang,
                            target_lang=target_lang,
                            model_name=model_name
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save progress for para {paragraph_num}: {e}")
                
                # Update progress UI
                # Count how many are done (not None)
                completed_count = sum(1 for p in translated_paragraphs if p is not None)
                if progress_callback:
                    progress_callback(completed_count, total_paragraphs)
                    
            return translation

        except ValueError as e:
            logger.error(f"Auth error at para {paragraph_num}: {e}")
            raise e
        except Exception as e:
            error_msg = f"[Translation error: {str(e)}]"
            error_text = f"{paragraph} {error_msg}"
            with progress_lock:
                translated_paragraphs[idx] = error_text
                failed_paragraphs.append(paragraph_num)
            logger.warning(f"Failed to translate para {paragraph_num}: {e}")
            return error_text

    # Prepare tasks
    # We only process paragraphs that are not yet translated (i.e. currently None in translated_paragraphs)
    # or starting from resume_from_index if appropriate.
    tasks = []
    for idx in range(resume_from_index, total_paragraphs):
        tasks.append(idx)
        
    try:
        max_workers = config.MAX_WORKERS
        if max_workers < 1:
            max_workers = 1
            
        # Capture Streamlit context if available
        # This is needed to access st.session_state and UI elements from threads
        ctx = None
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
            ctx = get_script_run_ctx()
        except ImportError:
            pass
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Helper to submit with context
            def submit_with_context(fn, *args, **kwargs):
                if ctx:
                    add_script_run_ctx(threading.current_thread(), ctx)
                return fn(*args, **kwargs)

            # We need to wrap the function execution to attach context inside the thread
            def execution_wrapper(idx):
                if ctx:
                    add_script_run_ctx(threading.current_thread(), ctx)
                return process_paragraph(idx)

            # Submit all tasks
            future_to_idx = {executor.submit(execution_wrapper, i): i for i in tasks}
            
            # Wait for completion
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                
                # Check for stop signal
                if stop_check and stop_check():
                    logger.info("Stop signal detected, cancelling pending tasks...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise TranslationStoppedException(f"Translation stopped by user")
                    
                try:
                    future.result()
                except TranslationStoppedException:
                    raise
                except Exception as e:
                    # Individual task errors are handled inside process_paragraph, 
                    # but if something escapes, catch it here.
                    logger.error(f"Unexpected error in thread for para {idx+1}: {e}")

    except TranslationStoppedException as e:
        logger.info(f"Translation stopped: {e}")
        # Save whatever we have
        raise e
            
    # Final check for failed paragraphs
    translated_text = '\n\n'.join([p for p in translated_paragraphs if p is not None])
    
    if failed_paragraphs:
        logger.warning(f"{len(failed_paragraphs)} paragraphs failed to translate: {failed_paragraphs}")
    else:
        logger.info(f"Successfully translated all {total_paragraphs} paragraphs")
    
    if progress_file_id:
        logger.info(f"Translation completed for file_id: {progress_file_id}")
    
    return translated_text

