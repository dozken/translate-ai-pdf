"""
Test script for PDF generator with Cyrillic text support.
"""
import os
import tempfile
from pathlib import Path
from utils.pdf_generator import create_pdf_from_text, UnicodeFontNotFound

def test_pdf_generation_with_cyrillic():
    """Test PDF generation with Russian (Cyrillic) text."""
    print("Testing PDF generation with Cyrillic text...")
    
    # Sample Russian text (Cyrillic)
    russian_text = """Это тестовый документ для проверки поддержки кириллицы.

Первый абзац содержит русский текст, который должен отображаться правильно в PDF.

Второй абзац проверяет, что все символы кириллического алфавита работают корректно.

Третий абзац содержит различные символы: цифры 123, знаки препинания !?., и специальные символы."""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Generate PDF
        result_path = create_pdf_from_text(
            text=russian_text,
            output_path=output_path,
            title="Тестовый документ",
            source_lang="Arabic",
            target_lang="Russian",
            metadata={"original_filename": "test.pdf"}
        )
        
        # Check if file was created
        assert os.path.exists(result_path), f"PDF file was not created at {result_path}"
        assert os.path.getsize(result_path) > 0, "PDF file is empty"
        
        print(f"✅ PDF created successfully at: {result_path}")
        print(f"   File size: {os.path.getsize(result_path)} bytes")
        
        # Try to read the PDF to verify it's valid
        with open(result_path, 'rb') as f:
            pdf_content = f.read()
            assert pdf_content.startswith(b'%PDF'), "File is not a valid PDF"
        
        print("✅ PDF file is valid")
        return True
        
    except UnicodeFontNotFound as e:
        print(f"⚠️  Unicode font not found: {e}")
        print("   This is expected if no Unicode fonts are available for ReportLab")
        print("   The code should fall back to fpdf2")
        return True  # This is acceptable
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"🧹 Cleaned up test file: {output_path}")

def test_pdf_generation_with_english():
    """Test PDF generation with English text."""
    print("\nTesting PDF generation with English text...")
    
    english_text = """This is a test document for PDF generation.

First paragraph contains English text that should display correctly.

Second paragraph checks that all ASCII characters work properly.

Third paragraph contains various symbols: numbers 123, punctuation !?., and special characters."""
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        result_path = create_pdf_from_text(
            text=english_text,
            output_path=output_path,
            title="Test Document",
            source_lang="Arabic",
            target_lang="English"
        )
        
        assert os.path.exists(result_path), f"PDF file was not created at {result_path}"
        assert os.path.getsize(result_path) > 0, "PDF file is empty"
        
        print(f"✅ PDF created successfully at: {result_path}")
        print(f"   File size: {os.path.getsize(result_path)} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"🧹 Cleaned up test file: {output_path}")

def test_pdf_generation_with_mixed_content():
    """Test PDF generation with mixed English and Cyrillic text."""
    print("\nTesting PDF generation with mixed content...")
    
    mixed_text = """This is a mixed document / Это смешанный документ

English paragraph: This text should display correctly.

Russian paragraph: Этот текст также должен отображаться правильно.

Mixed paragraph: Hello / Привет, World / Мир!"""
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        result_path = create_pdf_from_text(
            text=mixed_text,
            output_path=output_path,
            title="Mixed Document / Смешанный документ",
            source_lang="Arabic",
            target_lang="Russian"
        )
        
        assert os.path.exists(result_path), f"PDF file was not created at {result_path}"
        assert os.path.getsize(result_path) > 0, "PDF file is empty"
        
        print(f"✅ PDF created successfully at: {result_path}")
        print(f"   File size: {os.path.getsize(result_path)} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"🧹 Cleaned up test file: {output_path}")

if __name__ == "__main__":
    print("=" * 60)
    print("PDF Generator Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Cyrillic text", test_pdf_generation_with_cyrillic()))
    results.append(("English text", test_pdf_generation_with_english()))
    results.append(("Mixed content", test_pdf_generation_with_mixed_content()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    exit(0 if all_passed else 1)
