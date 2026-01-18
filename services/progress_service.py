"""
Progress service - handles translation progress management.
Extracted from app.py for better separation of concerns.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from utils.progress_storage import get_file_id, load_progress, delete_progress
from utils.logger_config import get_logger

logger = get_logger(__name__)


class ProgressService:
    """Service for managing translation progress."""

    @staticmethod
    def get_file_progress(filename: str, file_size: int) -> Optional[Dict[str, Any]]:
        """
        Get existing progress for a file.

        Args:
            filename: Original filename
            file_size: File size in bytes

        Returns:
            Progress dictionary or None if not found
        """
        current_file_id = get_file_id(filename, file_size)
        return load_progress(current_file_id)

    @staticmethod
    def format_progress_info(progress: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format progress information for display.

        Args:
            progress: Raw progress dictionary

        Returns:
            Formatted progress information
        """
        if not progress:
            return None

        completed = progress.get("completed_paragraphs", 0)
        total = progress.get("total_paragraphs", 0)
        percent = (completed / total * 100) if total > 0 else 0
        last_updated = progress.get("updated_at", "unknown")

        return {
            "completed": completed,
            "total": total,
            "percent": percent,
            "last_updated": last_updated,
            "should_show_resume_options": completed > 0 and completed < total,
            "should_show_partial_download": completed > 0,
        }

    @staticmethod
    def delete_progress_data(filename: str, file_size: int, reason: str = "") -> None:
        """
        Delete progress data for a file.

        Args:
            filename: Original filename
            file_size: File size in bytes
            reason: Reason for deletion (for logging)
        """
        current_file_id = get_file_id(filename, file_size)
        delete_progress(current_file_id, reason or "progress deleted")
        logger.info(f"Progress deleted for {filename}: {reason}")


# Global service instance
progress_service = ProgressService()
