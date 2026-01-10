# Best Practices: Paragraph Splitting for Translation

## Overview

This guide provides best practices for paragraph splitting in translation applications, specifically for Arabic-to-Russian PDF translation. It synthesizes research findings, industry standards, and practical recommendations.

## Core Principles

### 1. Preserve Semantic Coherence

**Principle**: Paragraphs should maintain semantic coherence and context.

**Why**: Translation quality depends on context. Splitting mid-thought reduces translation accuracy.

**Implementation**:
- Group related sentences together
- Split at natural topic boundaries
- Preserve paragraph structure from source document

### 2. Respect Document Structure

**Principle**: Maintain the original document's structure and formatting.

**Why**: Structure conveys meaning (headings, sections, lists).

**Implementation**:
- Preserve explicit paragraph breaks (`\n\n`)
- Maintain heading hierarchy
- Keep verse/chapter numbers with their content
- Preserve list structures

### 3. Balance Size and Context

**Principle**: Optimize paragraph size for both API constraints and translation quality.

**Why**: 
- API limits require size management
- Too small: loses context
- Too large: exceeds limits, harder to translate

**Implementation**:
- Target: 500-1500 characters
- Minimum: 100 characters
- Maximum: 2000 characters
- Average: 800-1200 characters

### 4. Use Hierarchical Segmentation

**Principle**: Apply multiple strategies in priority order.

**Why**: Different documents have different structures.

**Implementation**:
1. **Level 1**: Explicit breaks (double newlines)
2. **Level 2**: Layout cues (spacing, indentation)
3. **Level 3**: Linguistic cues (sentence boundaries)
4. **Level 4**: Fallback (size-based chunking)

## Size Guidelines

### Recommended Sizes

| Metric | Recommended | Rationale |
|--------|-------------|-----------|
| Minimum | 100-200 chars | Ensures sufficient context, avoids fragments |
| Target | 800-1200 chars | Optimal balance of context and API efficiency |
| Maximum | 2000 chars | Respects API limits, maintains coherence |
| Average | 1000 chars | Good overall balance |

### Size Distribution

**Ideal Distribution**:
- Tiny (< 100 chars): < 5%
- Small (100-500 chars): 10-20%
- Medium (500-1500 chars): 60-70%
- Large (1500-2000 chars): 10-20%
- Huge (> 2000 chars): 0%

**Red Flags**:
- > 30% tiny paragraphs: Over-segmentation
- > 10% huge paragraphs: Under-segmentation
- Average < 200 chars: Too aggressive splitting

## Language-Specific Considerations

### Arabic Text

**Challenges**:
- RTL (right-to-left) text flow
- Optional punctuation
- Rich morphology
- Verse numbers in religious texts

**Best Practices**:
1. **Use Language-Aware Tools**: spaCy Arabic model for sentence detection
2. **Handle Verse Numbers**: Group verses together, don't split on each number
3. **RTL Awareness**: Consider text direction in layout analysis
4. **Punctuation Patterns**: Account for Arabic punctuation (؟،)

**Example**:
```python
# Bad: Splits on every verse number
1. Verse text.
2. Another verse.
3. Yet another.

# Good: Groups verses together
1. Verse text. 2. Another verse. 3. Yet another.
```

### Russian Text

**Considerations**:
- Cyrillic script
- Different punctuation patterns
- Longer words (affects character counts)

**Best Practices**:
- Use appropriate sentence tokenization
- Account for longer average word length
- Consider Russian punctuation rules

## Implementation Strategies

### Strategy 1: Explicit Breaks (Priority 1)

**When to Use**: Documents with clear paragraph markers

**Implementation**:
```python
paragraphs = text.split('\n\n')
```

**Pros**: 
- Preserves original structure
- Fast and simple
- High accuracy for well-formatted docs

**Cons**: 
- Fails on poorly formatted PDFs
- May create very large paragraphs

### Strategy 2: Layout-Aware Splitting (Priority 2)

**When to Use**: PDFs with layout information available

**Implementation**:
- Use PDF coordinate information
- Detect visual groupings
- Analyze spacing and indentation

**Pros**:
- Handles complex layouts
- Preserves document structure
- Good for multi-column documents

**Cons**:
- Requires PDF structure data
- More complex implementation
- May not be available for all PDFs

### Strategy 3: Sentence-Based Grouping (Priority 3)

**When to Use**: Large paragraphs without clear breaks

**Implementation**:
1. Detect sentence boundaries (language-aware)
2. Group sentences to target size
3. Split only when necessary

**Pros**:
- Maintains semantic coherence
- Language-aware
- Good for continuous text

**Cons**:
- Requires sentence detection
- May miss paragraph boundaries
- Slower than simple splitting

### Strategy 4: Size-Based Chunking (Fallback)

**When to Use**: When other strategies fail

**Implementation**:
- Split by word count
- Target 70-80% of max size
- Preserve word boundaries

**Pros**:
- Always works
- Respects size limits
- Simple implementation

**Cons**:
- May split mid-sentence
- Loses semantic coherence
- Last resort only

## Common Pitfalls and Solutions

### Pitfall 1: Over-Segmentation

**Problem**: Creating too many tiny paragraphs (e.g., 681 paragraphs from 60K chars)

**Causes**:
- Splitting on every line break
- Pattern matching too broad
- Threshold too low

**Solution**:
- Increase substantial threshold (300 → 800 chars)
- Tighten pattern matching
- Require multiple indicators for split

### Pitfall 2: Under-Segmentation

**Problem**: Creating paragraphs that are too large (> 2000 chars)

**Causes**:
- Missing paragraph breaks
- Not splitting large paragraphs
- Threshold too high

**Solution**:
- Force split at max size
- Use sentence-based splitting
- Check paragraph sizes in final cleanup

### Pitfall 3: Splitting on Verse Numbers

**Problem**: Each verse becomes a separate paragraph

**Causes**:
- Pattern matches verse numbers
- No grouping logic for verses

**Solution**:
- Detect verse patterns
- Group consecutive verses
- Use verse-aware splitting

### Pitfall 4: Losing Document Structure

**Problem**: Headings, lists, and sections are lost

**Causes**:
- Not preserving formatting
- Aggressive merging
- No structure detection

**Solution**:
- Detect and preserve headings
- Maintain list structures
- Use layout information when available

## Configuration Recommendations

### Default Parameters

```python
min_length = 100          # Minimum paragraph size
max_paragraph_size = 2000  # Maximum paragraph size
target_size = 1000        # Target paragraph size
substantial_threshold = 800  # Minimum size before splitting
```

### Document Type Presets

**Religious Texts (Verse-Numbered)**:
```python
min_length = 200
max_paragraph_size = 2500
substantial_threshold = 1000
use_verse_aware = True
```

**Academic Papers**:
```python
min_length = 150
max_paragraph_size = 2000
substantial_threshold = 600
preserve_headings = True
```

**General Documents**:
```python
min_length = 100
max_paragraph_size = 2000
substantial_threshold = 800
```

## Quality Metrics

### Metrics to Track

1. **Paragraph Count**: Total number of paragraphs
2. **Average Size**: Mean paragraph size
3. **Size Distribution**: Histogram of paragraph sizes
4. **Over-Segmentation Rate**: % of paragraphs < 100 chars
5. **Under-Segmentation Rate**: % of paragraphs > 2000 chars
6. **Coverage**: % of original text included

### Target Metrics

- Paragraph count: Reasonable for document size (not hundreds)
- Average size: 800-1200 characters
- Over-segmentation: < 10%
- Under-segmentation: < 5%
- Coverage: 100%

### Monitoring

- Log metrics for each document
- Alert on over-segmentation (> 30%)
- Track translation quality correlation
- Monitor API usage (paragraph count)

## Implementation Checklist

### Basic Implementation

- [ ] Split on explicit breaks (`\n\n`)
- [ ] Filter very short paragraphs
- [ ] Handle large paragraphs (> max_size)
- [ ] Merge very short paragraphs
- [ ] Normalize whitespace

### Advanced Implementation

- [ ] Language-aware sentence detection
- [ ] Verse-aware grouping
- [ ] Layout-aware splitting
- [ ] Heading detection and preservation
- [ ] Size distribution tracking

### Quality Assurance

- [ ] Test with various document types
- [ ] Test with large documents (60K+ chars)
- [ ] Test with verse-numbered texts
- [ ] Monitor production metrics
- [ ] Collect user feedback

## Code Examples

### Basic Implementation

```python
def split_into_paragraphs(text: str, 
                         min_length: int = 100,
                         max_paragraph_size: int = 2000) -> List[str]:
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Split on explicit breaks
    paragraphs = text.split('\n\n')
    
    # Clean and filter
    cleaned = []
    for para in paragraphs:
        para = para.strip()
        para = re.sub(r'\s+', ' ', para)
        if len(para) >= min_length:
            cleaned.append(para)
    
    # Handle large paragraphs
    final = []
    for para in cleaned:
        if len(para) > max_paragraph_size:
            # Split by sentences
            final.extend(split_large_paragraph(para, max_paragraph_size))
        else:
            final.append(para)
    
    return final
```

### Conservative Approach

```python
def split_conservative(text: str,
                      substantial_threshold: int = 800,
                      max_paragraph_size: int = 2000) -> List[str]:
    # Only split if:
    # 1. Current paragraph is substantial (>= threshold)
    # 2. Adding next sentence would exceed max_size
    # 3. Clear paragraph boundary indicators
    
    # This prevents over-segmentation
    ...
```

## References

- [Research Findings](../research/paragraph_splitting_research.md)
- [Library Comparison](../research/library_comparison.md)
- [Current Implementation Analysis](../research/current_implementation_analysis.md)
- [Benchmark Results](../research/benchmark_results.md)

## Conclusion

Effective paragraph splitting requires:
1. **Hierarchical approach** with multiple strategies
2. **Language awareness** for Arabic text
3. **Size management** balancing context and API limits
4. **Structure preservation** maintaining document meaning
5. **Quality metrics** to monitor and improve

Follow these best practices to achieve optimal translation quality while respecting API constraints.
