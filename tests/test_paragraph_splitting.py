"""
Test suite for paragraph splitting functionality.

Tests various scenarios and measures quality metrics.
"""
import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.translator import split_into_paragraphs


class TestParagraphSplitting(unittest.TestCase):
    """Test cases for paragraph splitting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent / "test_data" / "paragraph_splitting"
    
    def load_test_file(self, filename):
        """Load a test file."""
        filepath = self.test_data_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def calculate_metrics(self, paragraphs):
        """Calculate quality metrics for paragraphs."""
        if not paragraphs:
            return {
                'count': 0,
                'avg_size': 0,
                'min_size': 0,
                'max_size': 0,
                'over_segmented': 0,
                'under_segmented': 0,
                'size_distribution': {}
            }
        
        sizes = [len(p) for p in paragraphs]
        avg_size = sum(sizes) / len(sizes)
        min_size = min(sizes)
        max_size = max(sizes)
        
        # Count over-segmented (< 100 chars) and under-segmented (> 2000 chars)
        over_segmented = sum(1 for s in sizes if s < 100)
        under_segmented = sum(1 for s in sizes if s > 2000)
        
        # Size distribution buckets
        distribution = {
            'tiny (< 100)': sum(1 for s in sizes if s < 100),
            'small (100-500)': sum(1 for s in sizes if 100 <= s < 500),
            'medium (500-1500)': sum(1 for s in sizes if 500 <= s < 1500),
            'large (1500-2000)': sum(1 for s in sizes if 1500 <= s <= 2000),
            'huge (> 2000)': sum(1 for s in sizes if s > 2000),
        }
        
        return {
            'count': len(paragraphs),
            'avg_size': avg_size,
            'min_size': min_size,
            'max_size': max_size,
            'over_segmented': over_segmented,
            'under_segmented': under_segmented,
            'over_segmented_rate': over_segmented / len(paragraphs) * 100,
            'under_segmented_rate': under_segmented / len(paragraphs) * 100,
            'size_distribution': distribution
        }
    
    def test_well_formatted_document(self):
        """Test splitting of well-formatted document with clear breaks."""
        text = self.load_test_file("well_formatted.txt")
        paragraphs = split_into_paragraphs(text)
        
        # Should have 3 paragraphs
        self.assertGreaterEqual(len(paragraphs), 2)
        self.assertLessEqual(len(paragraphs), 4)
        
        # All paragraphs should be reasonable size
        metrics = self.calculate_metrics(paragraphs)
        self.assertLess(metrics['over_segmented_rate'], 20)  # Less than 20% over-segmented
        self.assertEqual(metrics['under_segmented'], 0)  # No under-segmented
        
        print(f"\nWell-formatted document metrics: {metrics}")
    
    def test_large_single_paragraph(self):
        """Test splitting of large single paragraph document."""
        text = self.load_test_file("large_single_paragraph.txt")
        paragraphs = split_into_paragraphs(text)
        
        # Should create reasonable number of paragraphs (not hundreds)
        metrics = self.calculate_metrics(paragraphs)
        
        # Should not over-segment (not hundreds of tiny paragraphs)
        self.assertLess(metrics['count'], 50, 
                       f"Too many paragraphs: {metrics['count']} (expected < 50)")
        
        # Average size should be reasonable
        self.assertGreater(metrics['avg_size'], 200,
                          f"Average size too small: {metrics['avg_size']} (expected > 200)")
        
        # Should not have too many over-segmented paragraphs
        self.assertLess(metrics['over_segmented_rate'], 30,
                       f"Too many over-segmented: {metrics['over_segmented_rate']}%")
        
        print(f"\nLarge single paragraph metrics: {metrics}")
    
    def test_verse_numbered_text(self):
        """Test splitting of verse-numbered text."""
        text = self.load_test_file("verse_numbered.txt")
        paragraphs = split_into_paragraphs(text)
        
        # Should group verses together (not create 5 separate paragraphs)
        metrics = self.calculate_metrics(paragraphs)
        
        # Should have 1-2 paragraphs, not 5
        self.assertLessEqual(metrics['count'], 3,
                            f"Too many paragraphs: {metrics['count']} (expected <= 3)")
        
        # Should not over-segment
        self.assertLess(metrics['over_segmented_rate'], 50)
        
        print(f"\nVerse-numbered text metrics: {metrics}")
    
    def test_mixed_formatting(self):
        """Test splitting of document with mixed formatting."""
        text = self.load_test_file("mixed_formatting.txt")
        paragraphs = split_into_paragraphs(text)
        
        # Should handle mixed formatting reasonably
        metrics = self.calculate_metrics(paragraphs)
        
        # Should have reasonable number of paragraphs
        self.assertGreater(metrics['count'], 0)
        self.assertLess(metrics['count'], 10)
        
        # Should not over-segment
        self.assertLess(metrics['over_segmented_rate'], 40)
        
        print(f"\nMixed formatting metrics: {metrics}")
    
    def test_empty_text(self):
        """Test handling of empty text."""
        paragraphs = split_into_paragraphs("")
        self.assertEqual(len(paragraphs), 0)
        
        paragraphs = split_into_paragraphs("   ")
        self.assertEqual(len(paragraphs), 0)
    
    def test_very_short_text(self):
        """Test handling of very short text."""
        text = "This is a very short text."
        paragraphs = split_into_paragraphs(text, min_length=10)
        
        # Should return at least one paragraph if above min_length
        if len(text) >= 10:
            self.assertGreaterEqual(len(paragraphs), 1)
    
    def test_size_constraints(self):
        """Test that paragraphs respect size constraints."""
        # Create a large text
        text = "Sentence. " * 500  # ~5000 chars
        paragraphs = split_into_paragraphs(text, max_paragraph_size=2000)
        
        # All paragraphs should be <= max_paragraph_size * 1.5 (with some tolerance)
        for para in paragraphs:
            self.assertLessEqual(len(para), 3000,
                               f"Paragraph too large: {len(para)} chars")
        
        # Should have multiple paragraphs
        self.assertGreater(len(paragraphs), 1)
    
    def test_min_length_filtering(self):
        """Test that very short paragraphs are filtered or merged."""
        text = "Short. " * 5 + "\n\n" + "Another short. " * 5
        paragraphs = split_into_paragraphs(text, min_length=50)
        
        # Very short paragraphs should be filtered or merged
        for para in paragraphs:
            self.assertGreaterEqual(len(para), 30,  # Allow some tolerance
                                  f"Paragraph too short: {len(para)} chars")


def run_benchmark():
    """Run benchmark tests and print results."""
    print("=" * 80)
    print("Paragraph Splitting Benchmark")
    print("=" * 80)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParagraphSplitting)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("Benchmark Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result


if __name__ == "__main__":
    run_benchmark()
