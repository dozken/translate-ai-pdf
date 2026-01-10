"""
PDF text extraction utility for Arabic and other languages.
"""
import pdfplumber
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_file) -> Tuple[str, dict]:
    """
    Extract text from uploaded PDF file.
    
    Args:
        pdf_file: Uploaded file object (from Streamlit file_uploader)
        
    Returns:
        Tuple of (extracted_text, metadata_dict)
        metadata contains: page_count, char_count, word_count
    """
    logger.debug("Starting PDF text extraction")
    try:
        full_text = ""
        page_count = 0
        
        with pdfplumber.open(pdf_file) as pdf:
            page_count = len(pdf.pages)
            logger.debug(f"PDF opened: {page_count} pages found")
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                    logger.debug(f"Extracted text from page {page_num}: {len(page_text)} characters")
                else:
                    logger.warning(f"No text found on page {page_num}")
        
        # Clean up text
        full_text = full_text.strip()
        
        # Calculate statistics
        char_count = len(full_text)
        word_count = len(full_text.split()) if full_text else 0
        
        metadata = {
            "page_count": page_count,
            "char_count": char_count,
            "word_count": word_count
        }
        
        logger.info(f"PDF extraction completed: {page_count} pages, {char_count} chars, {word_count} words")
        return full_text, metadata
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
        raise Exception(f"Error extracting text from PDF: {str(e)}")



