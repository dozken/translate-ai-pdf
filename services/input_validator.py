"""
Input validation service - validates user inputs and sanitizes data.
Improves security by preventing injection and malformed data.
"""

import logging
import re
import os
from typing import Tuple, Optional, Dict, Any, Union
from pathlib import Path

from utils.logger_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom validation exception."""

    pass


class InputValidator:
    """Service for validating and sanitizing user inputs."""

    # Validation constants
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_PDF_EXTENSIONS = {".pdf"}
    SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
    MAX_FILENAME_LENGTH = 255

    @staticmethod
    def validate_pdf_file(pdf_file) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate uploaded PDF file with comprehensive security checks.

        Args:
            pdf_file: Uploaded file object

        Returns:
            Tuple of (is_valid, error_message, file_metadata)
        """
        if not pdf_file:
            return False, "No file uploaded", None

        # Extract file metadata safely
        try:
            filename = getattr(pdf_file, "name", "")
            file_size = getattr(pdf_file, "size", 0)
            file_type = getattr(pdf_file, "type", "")
        except Exception as e:
            logger.error(f"Error extracting file metadata: {e}")
            return False, "Invalid file object", None

        # Check filename
        if not filename:
            return False, "File has no name", None

        if len(filename) > InputValidator.MAX_FILENAME_LENGTH:
            return (
                False,
                f"Filename too long (max {InputValidator.MAX_FILENAME_LENGTH} characters)",
                None,
            )

        if not InputValidator.SAFE_FILENAME_PATTERN.match(filename):
            return False, "Filename contains invalid characters", None

        # Check extension
        file_path = Path(filename)
        file_extension = file_path.suffix.lower()

        if file_extension not in InputValidator.ALLOWED_PDF_EXTENSIONS:
            return False, f"Invalid file type '{file_extension}'. Only PDF files are allowed.", None

        # Check file size
        if file_size > InputValidator.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return (
                False,
                f"File size {size_mb:.1f}MB exceeds limit of {InputValidator.MAX_FILE_SIZE / (1024 * 1024)}MB",
                None,
            )

        if file_size == 0:
            return False, "File is empty", None

        # Validate MIME type if available
        if file_type and not file_type.lower().startswith("application/pdf"):
            return False, f"Invalid file type '{file_type}'. Must be a PDF file.", None

        # Return validated metadata
        return (
            True,
            "",
            {
                "filename": filename,
                "file_size": file_size,
                "file_extension": file_extension,
                "file_type": file_type,
                "size_mb": round(file_size / (1024 * 1024), 2),
            },
        )

    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 10000) -> str:
        """
        Sanitize text input to prevent injection.

        Args:
            text: Raw text input
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove potentially dangerous characters
        sanitized = text.strip()

        # Remove null bytes and control characters except newlines and tabs
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @staticmethod
    def validate_language_codes(source_lang: str, target_lang: str) -> Tuple[bool, str]:
        """
        Validate language codes.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Tuple of (is_valid, error_message)
        """
        supported_languages = [
            "Arabic",
            "Chinese",
            "English",
            "French",
            "German",
            "Russian",
            "Spanish",
            "Japanese",
            "Korean",
            "Portuguese",
            "Italian",
        ]

        if source_lang not in supported_languages:
            return False, f"Unsupported source language: {source_lang}"

        if target_lang not in supported_languages:
            return False, f"Unsupported target language: {target_lang}"

        if source_lang == target_lang:
            return False, "Source and target languages cannot be the same"

        return True, ""

    @staticmethod
    def validate_output_directory(output_dir: str) -> Tuple[bool, str, Optional[Path]]:
        """
        Validate and secure output directory path.

        Args:
            output_dir: Output directory path

        Returns:
            Tuple of (is_valid, error_message, secure_path)
        """
        if not output_dir:
            return True, "", None  # Use default

        try:
            # Convert to Path and resolve
            dir_path = Path(output_dir).resolve()

            # Prevent path traversal
            if ".." in output_dir:
                return False, "Path traversal detected", None

            # Check if within reasonable bounds
            current_dir = Path.cwd()
            try:
                dir_path.relative_to(current_dir)
            except ValueError:
                return False, "Output directory must be within current project", None

            # Create directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)

            # Check if directory is writable
            if not os.access(dir_path, os.W_OK):
                return False, f"Directory is not writable: {dir_path}", None

            return True, "", dir_path

        except Exception as e:
            return False, f"Invalid output directory: {str(e)}", None

    @staticmethod
    def validate_api_key(api_key: str, provider: str = "google") -> Tuple[bool, str]:
        """
        Validate API key format.

        Args:
            api_key: API key string
            provider: Provider name for validation rules

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key:
            return False, "API key is required"

        api_key = api_key.strip()

        if provider.lower() == "google":
            # Google API keys typically start with specific patterns
            if not api_key.startswith("AIza") or len(api_key) < 20:
                return False, "Invalid Google API key format"

        # General validation
        if len(api_key) > 500:
            return False, "API key too long"

        # Check for suspicious characters
        if not re.match(r"^[a-zA-Z0-9_\-]+$", api_key):
            return False, "API key contains invalid characters"

        return True, ""


# Global validator instance
input_validator = InputValidator()
