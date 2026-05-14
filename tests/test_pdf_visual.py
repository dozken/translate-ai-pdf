"""
Visual verification test - creates a PDF and provides instructions to check it manually.
"""

import os

from utils.pdf_generator import create_pdf_from_text


def create_test_pdf():
    """Create a test PDF with Cyrillic text for manual verification."""
    print("Creating test PDF with Cyrillic text...")

    # Sample Russian text with various Cyrillic characters
    russian_text = """Это тестовый документ для проверки поддержки кириллицы в PDF.

Первый абзац: АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ
Строчные буквы: абвгдеёжзийклмнопрстуфхцчшщъыьэюя

Второй абзац содержит числа: 0123456789

Третий абзац содержит знаки препинания: !?.,;:—«»""()[]{}'"

Четвертый абзац содержит смешанный текст: Hello, мир! 123 + 456 = 579

Пятый абзац проверяет длинные строки текста, которые должны правильно переноситься на новую строку в PDF документе. Это важно для читаемости документа."""

    # Create output in current directory for easy access
    output_path = "test_cyrillic_output.pdf"

    try:
        result_path = create_pdf_from_text(
            text=russian_text,
            output_path=output_path,
            title="Тестовый документ - Проверка кириллицы",
            source_lang="Arabic",
            target_lang="Russian",
            metadata={"original_filename": "test.pdf"},
        )

        print("\n✅ PDF created successfully!")
        print(f"   Location: {os.path.abspath(result_path)}")
        print(f"   File size: {os.path.getsize(result_path)} bytes")
        print("\n📋 Instructions for visual verification:")
        print(f"   1. Open the PDF file: {os.path.abspath(result_path)}")
        print("   2. Check that all Cyrillic text is visible and readable")
        print("   3. Verify there are NO black rectangles instead of text")
        print("   4. Check that all characters display correctly:")
        print("      - Uppercase: АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")
        print("      - Lowercase: абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
        print("      - Numbers: 0123456789")
        print("      - Punctuation: !?.,;:—«»" "()[]{}'\"")
        print("\n   If you see black rectangles, the font doesn't support Cyrillic.")
        print("   If all text is visible, the fix is working correctly! ✅")

        return result_path

    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("PDF Visual Verification Test")
    print("=" * 70)
    create_test_pdf()
    print("\n" + "=" * 70)
