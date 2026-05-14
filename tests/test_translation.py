"""
Test script for translation functionality using a sample paragraph from 65 الطلاق.pdf
"""
import os
from config import config
from utils.translator import translate_text_gemini, split_into_paragraphs
from utils.pdf_generator import create_pdf_from_text


def test_translation():
    """Test translation with a single paragraph from the PDF."""
    
    # First paragraph from 65 الطلاق.pdf
    sample_arabic_text = """بِسْمِ اللهُ الرَّحْمٰنِ الرَّحِيمِ
يَا أَيُّهَا النَّبِيُّ إِذَا طَلَّقْتُمُ النِّسَاءَ فَطَلَّقُوهُنَّ لِعِدَّتِهِنَّ وَأَحْصُوا الْعِدَّةَ وَاتَّقُوا اللهُ رَبَّكُمْ لَا تُخْرِجُوهُنَّ مِنْ بُيُوتِهِنَّ وَلَا يَخْرُجْنَ إِلاَّ أَنْ يَأْتِينَ بِفَاحِشَةٍ مُّبَيِّنَةٍ وَتِلْكَ خُذُودُ اللهُ وَمَنْ يَتَعَدَّ خُذُودُ اللهُ فَقَدْ ظَلَمَ نَفْسَهُ لَا تَدْرِي لَعَلَّ اللهُ يُحْدِثُ بَعْدَ ذَلِكَ أَمْراً (1)"""
    
    print("=" * 60)
    print("Translation Test - Single Paragraph")
    print("=" * 60)
    print(f"\nOriginal Arabic text ({len(sample_arabic_text)} characters):")
    print("-" * 60)
    print(sample_arabic_text)
    print("-" * 60)
    
    # Get API key
    api_key = config.GOOGLE_API_KEY
    
    if not api_key:
        print("\n❌ Error: GOOGLE_API_KEY environment variable not set")
        print("💡 Set it in your `.env` file or as an environment variable:")
        print("   export GOOGLE_API_KEY='your-key'")
        return
    
    print(f"\n✅ API key found: {api_key[:10]}...")
    
    # Test paragraph splitting
    print("\n📝 Testing paragraph splitting...")
    paragraphs = split_into_paragraphs(sample_arabic_text)
    print(f"   Found {len(paragraphs)} paragraph(s)")
    for i, para in enumerate(paragraphs, 1):
        print(f"   Paragraph {i}: {len(para)} characters")
    
    # Test translation
    print("\n🌐 Starting translation...")
    print("   This may take a few seconds...")
    
    try:
        def progress_callback(current, total):
            print(f"   Progress: {current}/{total} paragraphs translated", end='\r')
        
        translated_text = translate_text_gemini(
            sample_arabic_text,
            api_key,
            source_lang="Arabic",
            target_lang="Russian",
            progress_callback=progress_callback
        )
        
        print("\n" + "=" * 60)
        print("✅ Translation completed!")
        print("=" * 60)
        print(f"\nTranslated Russian text ({len(translated_text)} characters):")
        print("-" * 60)
        print(translated_text)
        print("-" * 60)
        
        # Test PDF generation
        print("\n📄 Testing PDF generation...")
        output_path = "test_translation_output.pdf"
        
        create_pdf_from_text(
            translated_text,
            output_path,
            title="Test Translation - سورة الطلاق",
            source_lang="Arabic",
            target_lang="Russian",
            metadata={"original_filename": "65 الطلاق.pdf"}
        )
        
        print(f"✅ PDF created successfully: {output_path}")
        print(f"   File size: {os.path.getsize(output_path)} bytes")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\n❌ Authentication Error: {str(e)}")
    except ImportError as e:
        print(f"\n❌ Missing Package: {str(e)}")
        print("💡 Install with: pip install -e .")
    except Exception as e:
        print(f"\n❌ Translation Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_translation()

