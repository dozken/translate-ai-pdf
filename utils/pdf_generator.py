"""
PDF generation utilities for creating PDF files from translated text.
"""
from datetime import datetime
from typing import Optional
import os
import logging
import platform

logger = logging.getLogger(__name__)


class UnicodeFontNotFound(Exception):
    """Exception raised when no Unicode font is found for ReportLab"""
    pass


def create_pdf_from_text(
    text: str, 
    output_path: str, 
    title: str = "Translated Document",
    source_lang: str = "Arabic",
    target_lang: str = "Russian",
    metadata: Optional[dict] = None,
    include_metadata: bool = False
) -> str:
    """
    Create a PDF file from translated text.
    
    Args:
        text: Translated text content
        output_path: Path where PDF will be saved
        title: Document title
        source_lang: Source language
        target_lang: Target language
        metadata: Optional additional metadata dictionary
        include_metadata: Whether to include metadata page (default: False)
        
    Returns:
        Path to created PDF file
    """
    logger.info(f"Creating PDF: {output_path}, title: {title}, {source_lang} -> {target_lang}, text length: {len(text)} chars")
    
    # Use custom output directory from env if specified
    pdf_output_dir = os.getenv("PDF_OUTPUT_DIR")
    if pdf_output_dir and not os.path.isabs(output_path):
        # If output_path is relative and PDF_OUTPUT_DIR is set, use it
        output_path = os.path.join(pdf_output_dir, os.path.basename(output_path))
        logger.debug(f"Using PDF_OUTPUT_DIR: {pdf_output_dir}")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    os.makedirs(output_dir, exist_ok=True)
    logger.debug(f"Output directory: {output_dir}")
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        
        # Register a Unicode font that supports Cyrillic
        # Try to find and register a system font
        unicode_font_name = 'Helvetica'  # Default fallback
        font_registered = False
        
        # Common system font paths for Unicode support (prioritize Cyrillic-supporting fonts)
        system_font_paths = []
        if platform.system() == 'Darwin':  # macOS
            system_font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',  # Best Cyrillic support
                '/Library/Fonts/Arial Unicode.ttf',
                '/System/Library/Fonts/Supplemental/NotoSansCJK-Regular.otf',
                '/System/Library/Fonts/Helvetica.ttc',
            ]
        elif platform.system() == 'Linux':
            system_font_paths = [
                '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',  # Excellent Cyrillic
                '/usr/share/fonts/truetype/noto/NotoSansCyrillic-Regular.ttf',  # Best for Cyrillic
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',  # Good Cyrillic
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Good Cyrillic
                '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
            ]
        elif platform.system() == 'Windows':
            system_font_paths = [
                'C:/Windows/Fonts/arialuni.ttf',  # Best Unicode/Cyrillic
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/times.ttf',  # Times New Roman supports Cyrillic
                'C:/Windows/Fonts/timesnr.ttf',
            ]
        
        # Try to register a Unicode font
        for font_path in system_font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                    unicode_font_name = 'UnicodeFont'
                    font_registered = True
                    logger.info(f"Registered Unicode font: {font_path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to register font {font_path}: {e}")
                    continue
        
        # If no system font found, we'll need to handle Unicode differently
        # ReportLab's default fonts don't support Cyrillic, so we'll fall back to fpdf2
        if not font_registered:
            logger.warning("No Unicode font found for ReportLab, will use fpdf2 fallback")
            # Force fallback to fpdf2 by raising a custom exception
            raise UnicodeFontNotFound("Unicode font not available, using fpdf2")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for PDF elements
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#000000',
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=unicode_font_name
        )
        
        # Normal text style (supports Unicode/Russian)
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            alignment=TA_LEFT,
            fontName=unicode_font_name,
            spaceAfter=6
        )
        
        # Heading style for detected headings
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor='#000000',
            spaceBefore=16,
            spaceAfter=10,
            fontName=unicode_font_name,
            fontNameBold=unicode_font_name
        )
        
        # Metadata style
        metadata_style = ParagraphStyle(
            'CustomMetadata',
            parent=styles['Normal'],
            fontSize=9,
            textColor='#666666',
            alignment=TA_CENTER,
            fontName=unicode_font_name
        )
        
        # Add title page only if metadata is included
        if include_metadata:
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.5*inch))
            
            # Add metadata
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata_text = f"Translation from {source_lang} to {target_lang}<br/>Generated on {date_str}"
            if metadata:
                if 'original_filename' in metadata:
                    metadata_text += f"<br/>Source: {metadata['original_filename']}"
            story.append(Paragraph(metadata_text, metadata_style))
            story.append(PageBreak())
        
        # Helper function to detect if a line is a heading
        def is_heading(line: str) -> bool:
            """Detect if a line looks like a heading"""
            line = line.strip()
            if not line:
                return False
            # Headings are usually short, may contain numbers, and end without punctuation
            if len(line) < 100 and not line.endswith(('.', '!', '?', ':', ';', ',')):
                # Check for common heading patterns
                if any(line.startswith(prefix) for prefix in ['Глава', 'Раздел', 'Часть', 'Глава', 'Сура', 'Аят']):
                    return True
                # Check if it's all caps or title case and short
                if line.isupper() and len(line.split()) <= 10:
                    return True
                # Check for numbered headings
                if line[0].isdigit() and len(line.split()) <= 8:
                    return True
            return False
        
        # Helper function to precalculate and clean paragraphs
        def precalculate_paragraphs(text: str) -> list:
            """Split text into paragraphs, filter empty ones, and return list"""
            raw_paragraphs = text.split('\n\n')
            cleaned_paragraphs = []
            for para in raw_paragraphs:
                para_cleaned = para.strip()
                if para_cleaned:  # Only include non-empty paragraphs
                    cleaned_paragraphs.append(para_cleaned)
            return cleaned_paragraphs
        
        # Precalculate paragraphs
        paragraphs = precalculate_paragraphs(text)
        total_paragraphs = len(paragraphs)
        logger.info(f"Precalculated {total_paragraphs} paragraphs for PDF generation")
        
        # Process paragraphs one by one
        for para_idx, para in enumerate(paragraphs, 1):
            lines = para.split('\n')
            # Check if first line is a heading
            if len(lines) > 1 and is_heading(lines[0]):
                # First line is heading
                heading_text = lines[0].strip()
                heading_escaped = heading_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"<b>{heading_escaped}</b>", heading_style))
                
                # Rest of the paragraph
                body_text = '\n'.join(lines[1:]).strip()
                if body_text:
                    body_escaped = body_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    body_escaped = body_escaped.replace('\n', '<br/>')
                    story.append(Paragraph(body_escaped, normal_style))
            else:
                # Regular paragraph
                para_escaped = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                para_escaped = para_escaped.replace('\n', '<br/>')
                story.append(Paragraph(para_escaped, normal_style))
            
            # Add spacing between paragraphs (but not after the last one)
            if para_idx < total_paragraphs:
                story.append(Spacer(1, 6))
        
        # Build PDF
        logger.debug("Building PDF with ReportLab")
        doc.build(story)
        logger.info(f"PDF created successfully with ReportLab: {output_path}")
        
        return output_path
        
    except (ImportError, UnicodeFontNotFound) as e:
        # UnicodeFontNotFound is raised when no Unicode font is found for ReportLab
        if isinstance(e, UnicodeFontNotFound):
            logger.warning("No Unicode font found for ReportLab, using fpdf2 fallback")
        else:
            logger.warning(f"ReportLab import error, trying fpdf2 fallback: {e}")
        pass
    except Exception as e:
        # Other exceptions - try fpdf2 as fallback
        logger.warning(f"ReportLab error: {e}, trying fpdf2 fallback", exc_info=True)
    
    # Fallback to fpdf2 if reportlab failed or Unicode font not found
    try:
        from fpdf import FPDF
        
        # Create PDF with Unicode support
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        
        # Better font detection for Cyrillic support
        font_name = 'Helvetica'  # Default fallback
        font_path_used = None
        try:
            # Try to find fpdf2 font directory
            import fpdf
            fpdf_path = os.path.dirname(fpdf.__file__)
            font_dir = os.path.join(fpdf_path, 'fonts')
            
            # Try DejaVu fonts (bundled with fpdf2) - good Cyrillic support
            dejavu_paths = [
                os.path.join(font_dir, 'DejaVuSans.ttf'),
                os.path.join(font_dir, 'DejaVuSansCondensed.ttf'),
            ]
            
            dejavu_found = False
            for font_path in dejavu_paths:
                if os.path.exists(font_path):
                    try:
                        pdf.add_font('DejaVu', '', font_path, uni=True)
                        pdf.add_font('DejaVu', 'B', font_path, uni=True)
                        font_name = 'DejaVu'
                        font_path_used = font_path
                        dejavu_found = True
                        logger.info(f"Using fpdf2 DejaVu font: {font_path} (excellent Cyrillic support)")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load DejaVu font {font_path}: {e}")
                        continue
            
            # Try system fonts that support Cyrillic
            if not dejavu_found:
                system_font_paths = []
                if platform.system() == 'Darwin':  # macOS
                    system_font_paths = [
                        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                        '/Library/Fonts/Arial Unicode.ttf',
                    ]
                elif platform.system() == 'Linux':
                    system_font_paths = [
                        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
                        '/usr/share/fonts/truetype/noto/NotoSansCyrillic-Regular.ttf',
                        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    ]
                elif platform.system() == 'Windows':
                    system_font_paths = [
                        'C:/Windows/Fonts/arialuni.ttf',
                        'C:/Windows/Fonts/arial.ttf',
                    ]
                
                for font_path in system_font_paths:
                    if os.path.exists(font_path):
                        try:
                            font_base_name = os.path.splitext(os.path.basename(font_path))[0]
                            pdf.add_font('SystemFont', '', font_path, uni=True)
                            pdf.add_font('SystemFont', 'B', font_path, uni=True)
                            font_name = 'SystemFont'
                            font_path_used = font_path
                            logger.info(f"Using system font: {font_path} (supports Cyrillic)")
                            break
                        except Exception as e:
                            logger.warning(f"Failed to load system font {font_path}: {e}")
                            continue
                
                if not font_path_used:
                    # Try system font names (may work on some systems)
                    system_font_names = ['Arial', 'Liberation Sans', 'DejaVu Sans', 'Times New Roman']
                    for sys_font in system_font_names:
                        try:
                            pdf.set_font(sys_font, size=12)
                            font_name = sys_font
                            logger.info(f"Using system font name: {sys_font}")
                            break
                        except:
                            continue
                    
                    if font_name == 'Helvetica':
                        pdf.set_font("Helvetica", size=12)
                        logger.warning("Using default Helvetica (may not support Cyrillic - black rectangles may appear)")
        except Exception as e:
            logger.warning(f"Font setup error: {e}, using default")
            pdf.set_font("Helvetica", size=12)
        
        # Add title and metadata only if requested
        if include_metadata:
            pdf.set_font(font_name, size=16, style='B')
            pdf.cell(0, 10, title, ln=True, align='C')
            pdf.ln(10)
            
            # Add metadata
            pdf.set_font(font_name, size=9)
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf.cell(0, 5, f"Translation from {source_lang} to {target_lang}", ln=True, align='C')
            pdf.cell(0, 5, f"Generated on {date_str}", ln=True, align='C')
            if metadata and 'original_filename' in metadata:
                pdf.cell(0, 5, f"Source: {metadata['original_filename']}", ln=True, align='C')
            pdf.ln(10)
        
        # Helper function to detect if a line is a heading
        def is_heading(line: str) -> bool:
            """Detect if a line looks like a heading"""
            line = line.strip()
            if not line:
                return False
            if len(line) < 100 and not line.endswith(('.', '!', '?', ':', ';', ',')):
                if any(line.startswith(prefix) for prefix in ['Глава', 'Раздел', 'Часть', 'Сура', 'Аят']):
                    return True
                if line.isupper() and len(line.split()) <= 10:
                    return True
                if line[0].isdigit() and len(line.split()) <= 8:
                    return True
            return False
        
        # Helper function to precalculate and clean paragraphs
        def precalculate_paragraphs(text: str) -> list:
            """Split text into paragraphs, filter empty ones, and return list"""
            raw_paragraphs = text.split('\n\n')
            cleaned_paragraphs = []
            for para in raw_paragraphs:
                para_cleaned = para.strip()
                if para_cleaned:  # Only include non-empty paragraphs
                    cleaned_paragraphs.append(para_cleaned)
            return cleaned_paragraphs
        
        # Precalculate paragraphs
        paragraphs = precalculate_paragraphs(text)
        total_paragraphs = len(paragraphs)
        logger.info(f"Precalculated {total_paragraphs} paragraphs for PDF generation (fpdf2)")
        
        # Add content with better formatting - process paragraphs one by one
        pdf.set_font(font_name, size=12)
        for para_idx, para in enumerate(paragraphs, 1):
            lines = para.split('\n')
            # Check if first line is a heading
            if len(lines) > 1 and is_heading(lines[0]):
                # First line is heading
                heading_text = lines[0].strip()
                pdf.set_font(font_name, size=14, style='B')
                pdf.multi_cell(0, 7, heading_text)
                pdf.ln(3)
                
                # Rest of the paragraph
                body_text = '\n'.join(lines[1:]).strip()
                if body_text:
                    pdf.set_font(font_name, size=12)
                    pdf.multi_cell(0, 6, body_text)
            else:
                # Regular paragraph
                para_clean = para.replace('\n', ' ')
                pdf.set_font(font_name, size=12)
                pdf.multi_cell(0, 6, para_clean)
            
            # Add spacing between paragraphs (but not after the last one)
            if para_idx < total_paragraphs:
                pdf.ln(6)
        
        # Save PDF
        logger.debug("Saving PDF with fpdf2")
        pdf.output(output_path)
        logger.info(f"PDF created successfully with fpdf2: {output_path}")
        return output_path
        
    except ImportError as e:
        logger.error(f"Required PDF library not found: {e}")
        raise ImportError(
            "PDF generation requires either 'reportlab' (with Unicode font) or 'fpdf2' package. "
            "Install with: pip install reportlab or pip install fpdf2"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error creating PDF: {error_msg}", exc_info=True)
        # Provide more specific error messages
        if "permission" in error_msg.lower():
            raise Exception(f"Permission denied when creating PDF at {output_path}. Check file permissions.")
        elif "disk" in error_msg.lower() or "space" in error_msg.lower():
            raise Exception(f"Insufficient disk space to create PDF.")
        else:
            raise Exception(f"Error creating PDF: {error_msg}")

