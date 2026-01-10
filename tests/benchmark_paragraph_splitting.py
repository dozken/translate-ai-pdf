"""
Benchmark script for comparing different paragraph splitting approaches.
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.translator import split_into_paragraphs
from utils.experimental.paragraph_splitters import (
    split_paragraphs_langchain_style,
    split_paragraphs_conservative,
    split_paragraphs_size_focused,
    split_paragraphs_verse_aware
)


def load_test_file(filename):
    """Load a test file."""
    filepath = Path(__file__).parent / "test_data" / "paragraph_splitting" / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def calculate_metrics(paragraphs, approach_name, text_length):
    """Calculate and return metrics for paragraphs."""
    if not paragraphs:
        return {
            'approach': approach_name,
            'count': 0,
            'avg_size': 0,
            'min_size': 0,
            'max_size': 0,
            'over_segmented': 0,
            'under_segmented': 0,
            'over_segmented_rate': 0,
            'under_segmented_rate': 0,
            'size_distribution': {},
            'coverage': 0
        }
    
    sizes = [len(p) for p in paragraphs]
    total_chars = sum(sizes)
    avg_size = sum(sizes) / len(sizes)
    min_size = min(sizes)
    max_size = max(sizes)
    
    over_segmented = sum(1 for s in sizes if s < 100)
    under_segmented = sum(1 for s in sizes if s > 2000)
    
    distribution = {
        'tiny (< 100)': sum(1 for s in sizes if s < 100),
        'small (100-500)': sum(1 for s in sizes if 100 <= s < 500),
        'medium (500-1500)': sum(1 for s in sizes if 500 <= s < 1500),
        'large (1500-2000)': sum(1 for s in sizes if 1500 <= s <= 2000),
        'huge (> 2000)': sum(1 for s in sizes if s > 2000),
    }
    
    return {
        'approach': approach_name,
        'count': len(paragraphs),
        'avg_size': round(avg_size, 1),
        'min_size': min_size,
        'max_size': max_size,
        'over_segmented': over_segmented,
        'under_segmented': under_segmented,
        'over_segmented_rate': round(over_segmented / len(paragraphs) * 100, 1),
        'under_segmented_rate': round(under_segmented / len(paragraphs) * 100, 1),
        'size_distribution': distribution,
        'coverage': round(total_chars / text_length * 100, 1) if text_length > 0 else 0
    }


def benchmark_approach(func, text, approach_name, **kwargs):
    """Benchmark a single approach."""
    start_time = time.time()
    try:
        paragraphs = func(text, **kwargs)
        elapsed = time.time() - start_time
        metrics = calculate_metrics(paragraphs, approach_name, len(text))
        metrics['time_ms'] = round(elapsed * 1000, 2)
        metrics['success'] = True
        return metrics
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'approach': approach_name,
            'success': False,
            'error': str(e),
            'time_ms': round(elapsed * 1000, 2)
        }


def run_benchmark():
    """Run benchmark on all test files."""
    test_files = [
        "well_formatted.txt",
        "large_single_paragraph.txt",
        "verse_numbered.txt",
        "mixed_formatting.txt"
    ]
    
    approaches = [
        ("Current Implementation", split_into_paragraphs, {}),
        ("LangChain Style", split_paragraphs_langchain_style, {'chunk_size': 2000, 'chunk_overlap': 200}),
        ("Conservative", split_paragraphs_conservative, {'substantial_threshold': 800}),
        ("Size Focused", split_paragraphs_size_focused, {'target_size': 1000}),
        ("Verse Aware", split_paragraphs_verse_aware, {}),
    ]
    
    results = {}
    
    print("=" * 100)
    print("Paragraph Splitting Benchmark Results")
    print("=" * 100)
    
    for test_file in test_files:
        print(f"\n{'=' * 100}")
        print(f"Test File: {test_file}")
        print(f"{'=' * 100}")
        
        text = load_test_file(test_file)
        print(f"Text length: {len(text)} characters\n")
        
        file_results = []
        
        for approach_name, func, kwargs in approaches:
            metrics = benchmark_approach(func, text, approach_name, **kwargs)
            file_results.append(metrics)
            
            if metrics['success']:
                print(f"\n{approach_name}:")
                print(f"  Paragraphs: {metrics['count']}")
                print(f"  Avg size: {metrics['avg_size']} chars")
                print(f"  Size range: {metrics['min_size']}-{metrics['max_size']} chars")
                print(f"  Over-segmented (< 100): {metrics['over_segmented']} ({metrics['over_segmented_rate']}%)")
                print(f"  Under-segmented (> 2000): {metrics['under_segmented']} ({metrics['under_segmented_rate']}%)")
                print(f"  Time: {metrics['time_ms']} ms")
                print(f"  Distribution: {metrics['size_distribution']}")
            else:
                print(f"\n{approach_name}: FAILED - {metrics.get('error', 'Unknown error')}")
        
        results[test_file] = file_results
    
    return results


def print_summary(results):
    """Print summary of benchmark results."""
    print("\n" + "=" * 100)
    print("Summary")
    print("=" * 100)
    
    # Find best approach for each metric
    for test_file, file_results in results.items():
        print(f"\n{test_file}:")
        
        successful = [r for r in file_results if r.get('success')]
        if not successful:
            print("  No successful approaches")
            continue
        
        # Best by paragraph count (closest to ideal: 5-20 for most cases)
        best_count = min(successful, key=lambda x: abs(x['count'] - 10))
        print(f"  Best paragraph count (closest to 10): {best_count['approach']} ({best_count['count']} paragraphs)")
        
        # Best by average size (closest to 1000)
        best_avg = min(successful, key=lambda x: abs(x['avg_size'] - 1000))
        print(f"  Best average size (closest to 1000): {best_avg['approach']} ({best_avg['avg_size']} chars)")
        
        # Best by over-segmentation rate (lowest)
        best_over = min(successful, key=lambda x: x['over_segmented_rate'])
        print(f"  Lowest over-segmentation: {best_over['approach']} ({best_over['over_segmented_rate']}%)")
        
        # Best by speed
        best_speed = min(successful, key=lambda x: x['time_ms'])
        print(f"  Fastest: {best_speed['approach']} ({best_speed['time_ms']} ms)")


if __name__ == "__main__":
    results = run_benchmark()
    print_summary(results)
    
    # Save results to file
    import json
    output_file = Path(__file__).parent.parent / "docs" / "research" / "benchmark_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to JSON-serializable format
    json_results = {}
    for test_file, file_results in results.items():
        json_results[test_file] = []
        for result in file_results:
            json_result = {k: v for k, v in result.items() if k != 'size_distribution'}
            json_result['size_distribution'] = result.get('size_distribution', {})
            json_results[test_file].append(json_result)
    
    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
