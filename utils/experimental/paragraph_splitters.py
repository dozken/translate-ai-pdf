"""
Experimental paragraph splitting implementations.

This module contains alternative approaches to paragraph splitting for comparison
and benchmarking purposes.
"""
import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def split_paragraphs_langchain_style(
    text: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
    min_length: int = 50
) -> List[str]:
    """
    LangChain-style recursive character text splitter.
    
    Uses hierarchical splitting with separators in priority order.
    """
    if not text or not text.strip():
        return []
    
    # Normalize text
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    def _split_recursive(text: str, separators: List[str]) -> List[str]:
        """Recursively split text using separators."""
        if not text.strip():
            return []
        
        # Try each separator in order
        for sep in separators:
            if sep in text:
                splits = text.split(sep)
                # Filter out empty splits
                splits = [s.strip() for s in splits if s.strip()]
                
                # If we got multiple splits, process each
                if len(splits) > 1:
                    result = []
                    for split in splits:
                        result.extend(_split_recursive(split, separators[separators.index(sep) + 1:]))
                    return result
        
        # No separator found, return as-is if within size limit
        if len(text) <= chunk_size:
            return [text] if len(text) >= min_length else []
        else:
            # Split by words if too large
            words = text.split()
            chunks = []
            current_chunk = []
            current_size = 0
            
            for word in words:
                word_size = len(word) + 1
                if current_size + word_size > chunk_size and current_chunk:
                    chunk_text = ' '.join(current_chunk).strip()
                    if len(chunk_text) >= min_length:
                        chunks.append(chunk_text)
                    current_chunk = [word]
                    current_size = len(word)
                else:
                    current_chunk.append(word)
                    current_size += word_size
            
            if current_chunk:
                chunk_text = ' '.join(current_chunk).strip()
                if len(chunk_text) >= min_length:
                    chunks.append(chunk_text)
            
            return chunks
    
    separators = ["\n\n", "\n", ". ", " ", ""]
    paragraphs = _split_recursive(text, separators)
    
    # Add overlap between chunks
    if chunk_overlap > 0 and len(paragraphs) > 1:
        overlapped = [paragraphs[0]]
        for i in range(1, len(paragraphs)):
            prev = paragraphs[i - 1]
            curr = paragraphs[i]
            
            # Take last chunk_overlap chars from previous
            if len(prev) > chunk_overlap:
                overlap_text = prev[-chunk_overlap:]
                overlapped.append(overlap_text + " " + curr)
            else:
                overlapped.append(curr)
        
        paragraphs = overlapped
    
    return paragraphs


def split_paragraphs_conservative(
    text: str,
    min_length: int = 50,
    max_paragraph_size: int = 2000,
    substantial_threshold: int = 800
) -> List[str]:
    """
    Conservative splitting approach with higher thresholds.
    
    Only splits when there are very clear indicators and substantial paragraphs.
    """
    if not text or not text.strip():
        return []
    
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strategy 1: Split on double newlines
    paragraphs = text.split('\n\n')
    cleaned_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        para = re.sub(r'\s+', ' ', para)
        if len(para) >= min_length:
            cleaned_paragraphs.append(para)
    
    # If we got multiple reasonable paragraphs, return them
    if len(cleaned_paragraphs) > 1:
        # Merge very short paragraphs
        merged = []
        for para in cleaned_paragraphs:
            if len(para) < min_length * 2 and merged:
                merged[-1] = merged[-1] + " " + para
            else:
                merged.append(para)
        cleaned_paragraphs = merged
    
    # If we only got 1 paragraph and it's very large, use fallback
    if len(cleaned_paragraphs) == 1 and len(cleaned_paragraphs[0]) > max_paragraph_size:
        large_text = cleaned_paragraphs[0]
        cleaned_paragraphs = []
        
        # Strategy 2: Split on sentence boundaries with higher threshold
        sentence_pattern = r'([.!?])\s+'
        parts = re.split(sentence_pattern, large_text)
        
        sentences = []
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                sentence = parts[i] + parts[i + 1]
            else:
                sentence = parts[i] if i < len(parts) else ""
            sentence = sentence.strip()
            if sentence and len(sentence) >= 10:
                sentences.append(sentence)
        
        # Group sentences with higher threshold
        if sentences:
            current_para = ""
            target_size = max_paragraph_size * 0.7
            
            for sentence in sentences:
                potential_para = current_para + " " + sentence if current_para else sentence
                
                # Only split if current para is substantial AND adding would exceed target
                if (current_para and 
                    len(current_para) >= substantial_threshold and 
                    len(potential_para) > target_size):
                    if len(current_para) >= min_length:
                        cleaned_paragraphs.append(current_para)
                    current_para = sentence
                else:
                    current_para = potential_para
                
                # Force split if exceeds max
                if len(current_para) > max_paragraph_size:
                    words = current_para.split()
                    mid_point = len(words) // 2
                    first_half = ' '.join(words[:mid_point])
                    second_half = ' '.join(words[mid_point:])
                    
                    if len(first_half) >= min_length:
                        cleaned_paragraphs.append(first_half)
                    current_para = second_half
            
            if current_para and len(current_para) >= min_length:
                cleaned_paragraphs.append(current_para)
        
        # Fallback to word-based if needed
        if len(cleaned_paragraphs) == 0 or (len(cleaned_paragraphs) == 1 and 
                                           len(cleaned_paragraphs[0]) > max_paragraph_size):
            words = large_text.split()
            current_chunk = []
            current_size = 0
            target_chunk_size = max_paragraph_size * 0.8
            
            for word in words:
                word_size = len(word) + 1
                if current_size + word_size > target_chunk_size and current_chunk:
                    chunk_text = ' '.join(current_chunk).strip()
                    if len(chunk_text) >= min_length:
                        cleaned_paragraphs.append(chunk_text)
                    current_chunk = [word]
                    current_size = len(word)
                else:
                    current_chunk.append(word)
                    current_size += word_size
            
            if current_chunk:
                chunk_text = ' '.join(current_chunk).strip()
                if len(chunk_text) >= min_length:
                    cleaned_paragraphs.append(chunk_text)
    
    # Final cleanup
    final_paragraphs = []
    for para in cleaned_paragraphs:
        para = re.sub(r'\s+', ' ', para).strip()
        
        if len(para) > max_paragraph_size * 1.5:
            # Split very large paragraphs
            words = para.split()
            current_chunk = []
            current_size = 0
            target_size = max_paragraph_size * 0.9
            
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
            # Merge very short paragraphs
            if len(para) < min_length * 2 and final_paragraphs and len(final_paragraphs[-1]) < max_paragraph_size * 0.7:
                final_paragraphs[-1] = final_paragraphs[-1] + " " + para
            else:
                final_paragraphs.append(para)
    
    return final_paragraphs


def split_paragraphs_size_focused(
    text: str,
    min_length: int = 50,
    target_size: int = 1000,
    max_size: int = 2000
) -> List[str]:
    """
    Size-focused approach that prioritizes consistent paragraph sizes.
    
    Groups content to achieve target size, splitting only when necessary.
    """
    if not text or not text.strip():
        return []
    
    # Normalize
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # First, split on explicit breaks
    initial_paragraphs = text.split('\n\n')
    paragraphs = []
    
    for para in initial_paragraphs:
        para = para.strip()
        para = re.sub(r'\s+', ' ', para)
        if len(para) >= min_length:
            paragraphs.append(para)
    
    # Group paragraphs to achieve target size
    grouped = []
    current_group = ""
    
    for para in paragraphs:
        potential_group = current_group + " " + para if current_group else para
        
        # If adding this para would exceed max_size, start new group
        if len(potential_group) > max_size and current_group:
            if len(current_group) >= min_length:
                grouped.append(current_group)
            current_group = para
        # If current group is below target, keep adding
        elif len(current_group) < target_size:
            current_group = potential_group
        # If current group is at target, start new group
        else:
            if len(current_group) >= min_length:
                grouped.append(current_group)
            current_group = para
    
    # Add last group
    if current_group and len(current_group) >= min_length:
        grouped.append(current_group)
    
    # For paragraphs that are still too large, split by sentences
    final_paragraphs = []
    for para in grouped:
        if len(para) > max_size:
            # Split by sentences
            sentence_pattern = r'([.!?])\s+'
            parts = re.split(sentence_pattern, para)
            
            sentences = []
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    sentence = parts[i] + parts[i + 1]
                else:
                    sentence = parts[i] if i < len(parts) else ""
                sentence = sentence.strip()
                if sentence:
                    sentences.append(sentence)
            
            # Group sentences to target size
            current = ""
            for sentence in sentences:
                potential = current + " " + sentence if current else sentence
                if len(potential) > max_size and current:
                    if len(current) >= min_length:
                        final_paragraphs.append(current)
                    current = sentence
                else:
                    current = potential
            
            if current and len(current) >= min_length:
                final_paragraphs.append(current)
        else:
            final_paragraphs.append(para)
    
    return final_paragraphs


def split_paragraphs_verse_aware(
    text: str,
    min_length: int = 50,
    max_paragraph_size: int = 2000
) -> List[str]:
    """
    Verse-aware splitting that groups verse-numbered lines together.
    
    Specifically handles texts with verse numbers (common in Arabic religious texts).
    """
    if not text or not text.strip():
        return []
    
    # Normalize
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Split on explicit breaks first
    paragraphs = text.split('\n\n')
    cleaned = []
    
    for para in paragraphs:
        para = para.strip()
        para = re.sub(r'\s+', ' ', para)
        if len(para) >= min_length:
            cleaned.append(para)
    
    # If we have multiple paragraphs, check for verse patterns
    if len(cleaned) > 1:
        # Check if paragraphs look like verses (start with numbers)
        verse_pattern = re.compile(r'^\d+[\.\)]\s')
        grouped = []
        current_group = []
        
        for para in cleaned:
            if verse_pattern.match(para):
                # This looks like a verse, group with previous verses
                current_group.append(para)
            else:
                # Not a verse, finalize current group and start new
                if current_group:
                    grouped_text = " ".join(current_group)
                    if len(grouped_text) >= min_length:
                        grouped.append(grouped_text)
                    current_group = []
                grouped.append(para)
        
        # Add last group
        if current_group:
            grouped_text = " ".join(current_group)
            if len(grouped_text) >= min_length:
                grouped.append(grouped_text)
        
        cleaned = grouped
    
    # Handle large paragraphs
    final_paragraphs = []
    for para in cleaned:
        if len(para) > max_paragraph_size:
            # Split large paragraphs by sentences, but try to keep verses together
            sentence_pattern = r'([.!?])\s+'
            parts = re.split(sentence_pattern, para)
            
            sentences = []
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    sentence = parts[i] + parts[i + 1]
                else:
                    sentence = parts[i] if i < len(parts) else ""
                sentence = sentence.strip()
                if sentence:
                    sentences.append(sentence)
            
            # Group sentences
            current = ""
            target_size = max_paragraph_size * 0.7
            
            for sentence in sentences:
                potential = current + " " + sentence if current else sentence
                if len(potential) > target_size and current:
                    if len(current) >= min_length:
                        final_paragraphs.append(current)
                    current = sentence
                else:
                    current = potential
            
            if current and len(current) >= min_length:
                final_paragraphs.append(current)
        else:
            final_paragraphs.append(para)
    
    return final_paragraphs
