"""
Translation service - handles all translation-related business logic.
Extracted from app.py for better separation of concerns.
"""

import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import concurrent.futures

from config import config
from utils.translator import (
    translate_text_gemini,
    split_into_paragraphs,
    TranslationStoppedException,
)
from utils.progress_storage import (
    get_file_id,
    load_progress,
    delete_progress,
    get_translated_text_from_progress,
)
from utils.pdf_generator import create_pdf_from_text
from utils.logger_config import get_logger

logger = get_logger(__name__)


class TranslationService:
    """Service for managing translation operations."""

    def __init__(self):
        self.translation_in_progress = False
        self.current_translations = {}  # Track active translations by file_id

    def start_translation(
        self,
        extracted_text: str,
        google_api_key: str,
        filename: str,
        file_size: int,
        source_lang: str = None,
        target_lang: str = None,
        progress_callback: Optional[Callable] = None,
        stream_callback: Optional[Callable] = None,
        resume_from_index: int = 0,
        stop_check: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Start translation process with progress tracking.

        Returns:
            Dictionary with translation results and metadata
        """
        if not source_lang:
            source_lang = config.SOURCE_LANGUAGE
        if not target_lang:
            target_lang = config.TARGET_LANGUAGE

        file_id = get_file_id(filename, file_size)
        self.current_translations[file_id] = {"started_at": datetime.now(), "status": "translating"}

        try:
            # Split text into paragraphs
            paragraphs_list = split_into_paragraphs(extracted_text)
            paragraph_count = len(paragraphs_list)
            if paragraph_count == 0:
                paragraph_count = 1

            logger.info(
                f"Starting translation: {len(extracted_text)} chars, "
                f"{paragraph_count} paragraphs, resume_from: {resume_from_index}"
            )

            # Perform translation
            enable_streaming = config.ENABLE_STREAMING
            translated_text = translate_text_gemini(
                extracted_text,
                google_api_key,
                source_lang=source_lang,
                target_lang=target_lang,
                progress_callback=progress_callback,
                stream=enable_streaming,
                stream_callback=stream_callback if enable_streaming else None,
                progress_file_id=file_id,
                resume_from_index=resume_from_index,
                stop_check=stop_check,
            )

            # Generate PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = filename.split(".")[0] if "." in filename else filename
            pdf_filename = f"translated_{base_name}_{timestamp}.pdf"

            output_dir = config.get_pdf_output_dir()
            pdf_path = str(output_dir / pdf_filename)

            create_pdf_from_text(
                translated_text,
                pdf_path,
                title=f"Translated {filename}",
                source_lang=source_lang,
                target_lang=target_lang,
                metadata={
                    "original_filename": filename,
                    "file_id": file_id,
                    "translation_timestamp": timestamp,
                },
            )

            # Clean up progress and mark complete
            delete_progress(file_id, reason="translation completed")
            self.current_translations[file_id]["status"] = "completed"
            self.current_translations[file_id]["completed_at"] = datetime.now()

            return {
                "success": True,
                "translated_text": translated_text,
                "pdf_path": pdf_path,
                "pdf_filename": pdf_filename,
                "file_id": file_id,
                "paragraph_count": paragraph_count,
                "character_count": len(translated_text),
            }

        except TranslationStoppedException as e:
            logger.info(f"Translation stopped for file {filename}: {e}")
            self.current_translations[file_id]["status"] = "stopped"
            raise

        except Exception as e:
            logger.error(f"Translation failed for {filename}: {e}", exc_info=True)
            self.current_translations[file_id]["status"] = "failed"
            self.current_translations[file_id]["error"] = str(e)
            raise

    def get_translation_status(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of translation by file ID."""
        return self.current_translations.get(file_id)

    def cancel_translation(self, file_id: str) -> bool:
        """Cancel an active translation."""
        if file_id in self.current_translations:
            self.current_translations[file_id]["status"] = "cancelled"
            return True
        return False

    def get_partial_pdf(self, filename: str, file_size: int) -> Optional[Dict[str, Any]]:
        """Generate partial PDF from existing progress."""
        current_file_id = get_file_id(filename, file_size)
        existing_progress = load_progress(current_file_id)

        if not existing_progress:
            return None

        completed = existing_progress.get("completed_paragraphs", 0)
        total = existing_progress.get("total_paragraphs", 0)

        if completed == 0:
            return None

        try:
            translated_text = get_translated_text_from_progress(existing_progress)
            output_dir = config.get_pdf_output_dir()
            base_name = filename.split(".")[0] if "." in filename else filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"translated_{base_name}_partial_{timestamp}.pdf"
            pdf_path = str(output_dir / pdf_filename)

            source_lang = existing_progress.get("source_lang", config.SOURCE_LANGUAGE)
            target_lang = existing_progress.get("target_lang", config.TARGET_LANGUAGE)

            create_pdf_from_text(
                translated_text,
                pdf_path,
                title=f"Partial Translation - {completed} of {total} paragraphs",
                source_lang=source_lang,
                target_lang=target_lang,
                metadata={
                    "original_filename": filename,
                    "partial_translation": True,
                    "completed_paragraphs": completed,
                    "total_paragraphs": total,
                },
            )

            return {
                "pdf_path": pdf_path,
                "pdf_filename": pdf_filename,
                "completed": completed,
                "total": total,
            }

        except Exception as e:
            logger.error(f"Error generating partial PDF: {e}", exc_info=True)
            return None


# Global service instance
translation_service = TranslationService()
