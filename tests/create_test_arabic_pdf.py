"""
Standalone script to create a test PDF with Arabic text.
This script does not modify the main application code.
"""
import os
from pathlib import Path
from utils.pdf_generator import create_pdf_from_text

# Two paragraphs of Arabic text
arabic_text = """بِسْمِ اللهِ الرَّحْمٰنِ الرَّحِيمِ

يَا أَيُّهَا النَّبِيُّ إِذَا طَلَّقْتُمُ النِّسَاءَ فَطَلِّقُوهُنَّ لِعِدَّتِهِنَّ وَأَحْصُوا الْعِدَّةَ وَاتَّقُوا اللهُ رَبَّكُمْ لَا تُخْرِجُوهُنَّ مِنْ بُيُوتِهِنَّ وَلَا يَخْرُجْنَ إِلَّا أَنْ يَأْتِينَ بِفَاحِشَةٍ مُبَيِّنَةٍ وَتِلْكَ حُدُودُ اللهُ وَمَنْ يَتَعَدَّ حُدُودُ اللهُ فَقَدْ ظَلَمَ نَفْسَهُ لَا تَدْرِي لَعَلَّ اللهُ يُحْدِثُ بَعْدَ ذَلِكَ أَمْراً (1)

وَاللَّاتِي يَئِسْنَ مِنَ الْمَحِيضِ مِنْ نِسَائِكُمْ إِنِ ارْتَبْتُمْ فَعِدَّتُهُنَّ ثَلَاثَةُ أَشْهُرٍ وَاللَّاتِي لَمْ يَحِضْنَ وَأُولَاتُ الْأَحْمَالِ أَجَلُهُنَّ أَنْ يَضَعْنَ حَمْلَهُنَّ وَمَنْ يَتَّقِ اللَّهَ يَجْعَلْ لَهُ مِنْ أَمْرِهِ يُسْراً (4)"""

# Get Downloads folder
home = Path.home()
downloads_folder = home / "Downloads"

# Create output filename
output_path = downloads_folder / "test_arabic_document.pdf"

print("Creating PDF with Arabic text...")
print(f"Output location: {output_path}")

try:
    # Create PDF
    result_path = create_pdf_from_text(
        text=arabic_text,
        output_path=str(output_path),
        title="Test Arabic Document",
        source_lang="Arabic",
        target_lang="Arabic",
        metadata={"original_filename": "test_arabic.txt"},
        include_metadata=False
    )
    
    print(f"✅ PDF created successfully!")
    print(f"   Location: {result_path}")
    print(f"   File size: {os.path.getsize(result_path)} bytes")
    
except Exception as e:
    print(f"❌ Error creating PDF: {e}")
    import traceback
    traceback.print_exc()
