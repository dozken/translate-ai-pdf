"""
PDF service - handles PDF processing and text extraction.
Extracted from app.py for better separation of concerns.
"""

import logging
from typing import Tuple, Dict, Any
from pathlib import Path

from utils.pdf_processor import extract_text_from_pdf
from utils.logger_config import get_logger

logger = get_logger(__name__)


class PDFService:
    """Service for handling PDF operations."""

    @staticmethod
    def process_uploaded_pdf(pdf_file) -> Dict[str, Any]:
        """
        Process uploaded PDF file and extract metadata.

        Args:
            pdf_file: Uploaded file object from Streamlit

        Returns:
            Dictionary with extracted text and metadata
        """
        logger.info(f"Processing PDF: {getattr(pdf_file, 'name', 'unknown')}")

        try:
            extracted_text, metadata = extract_text_from_pdf(pdf_file)

            if not extracted_text:
                logger.warning("No text extracted from PDF")
                return {
                    "success": False,
                    "error": "No text could be extracted from the PDF. The file might be image-based or corrupted.",
                    "metadata": None,
                }

            logger.info(
                f"PDF processed successfully: {metadata['page_count']} pages, "
                f"{metadata['char_count']} chars, {metadata['word_count']} words"
            )

            return {"success": True, "extracted_text": extracted_text, "metadata": metadata}

        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            return {"success": False, "error": f"Error processing PDF: {str(e)}", "metadata": None}

    @staticmethod
    def validate_pdf_file(pdf_file) -> Tuple[bool, str]:
        """
        Validate uploaded PDF file.

        Args:
            pdf_file: Uploaded file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pdf_file:
            return False, "No file uploaded"

        # Check file extension
        filename = getattr(pdf_file, "name", "")
        if not filename.lower().endswith(".pdf"):
            return False, "Please upload a PDF file"

        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        file_size = getattr(pdf_file, "size", 0)
        if file_size > max_size:
            return (
                False,
                f"File size exceeds 50MB limit. Current size: {file_size / (1024 * 1024):.1f}MB",
            )

        if file_size == 0:
            return False, "File is empty"

        return True, ""


# Global service instance
pdf_service = PDFService()
