"""
Error handling service - provides secure error handling and logging.
Prevents information disclosure and provides user-friendly error messages.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from enum import Enum

from utils.logger_config import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for user display."""

    LOW = "info"
    MEDIUM = "warning"
    HIGH = "error"
    CRITICAL = "error"


class TranslationError(Exception):
    """Custom translation exception with severity."""

    def __init__(
        self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: str = ""
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.details = details


class ErrorHandler:
    """Service for handling errors securely and informatively."""

    # Safe error messages (don't expose internal details)
    SAFE_ERROR_MESSAGES = {
        "pdf_processing": "Unable to process the PDF file. Please ensure it's a valid PDF document.",
        "api_authentication": "Authentication failed. Please check your API key configuration.",
        "api_rate_limit": "Rate limit exceeded. Please wait a moment and try again.",
        "api_network": "Network error. Please check your internet connection.",
        "translation_failed": "Translation failed. Please try again later.",
        "file_validation": "Invalid file. Please upload a valid PDF file.",
        "permission_denied": "Permission denied. Please check file and directory permissions.",
        "disk_space": "Insufficient disk space. Please free up space and try again.",
        "timeout": "Operation timed out. Please try again.",
        "configuration": "Configuration error. Please check your settings.",
        "unknown": "An unexpected error occurred. Please try again.",
    }

    @staticmethod
    def handle_error(
        error: Exception, context: str = "unknown", user_facing: bool = True
    ) -> Dict[str, Any]:
        """
        Handle error with secure logging and user-friendly messages.

        Args:
            error: The exception that occurred
            context: Context where error occurred
            user_facing: Whether this will be shown to users

        Returns:
            Dictionary with error information
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Log full error details for debugging
        logger.error(f"Error in {context}: {error_type} - {error_message}", exc_info=True)

        if not user_facing:
            return {
                "success": False,
                "error_type": error_type,
                "error_message": error_message,
                "show_to_user": False,
            }

        # Determine safe error message
        safe_message = ErrorHandler._get_safe_message(context, error_type, error_message)

        # Log security-relevant errors
        if ErrorHandler._is_security_relevant(error_type):
            logger.warning(f"Security-relevant error in {context}: {error_type}")

        return {
            "success": False,
            "error_type": error_type,
            "safe_message": safe_message,
            "user_message": safe_message,
            "context": context,
            "show_to_user": True,
            "severity": ErrorHandler._get_severity(error_type).value,
        }

    @staticmethod
    def _get_safe_message(context: str, error_type: str, original_message: str) -> str:
        """Get safe user-facing error message."""
        # Map context to safe messages
        context_mappings = {
            "pdf_processing": ["pdf_processing"],
            "api_call": ["api_authentication", "api_rate_limit", "api_network"],
            "file_upload": ["file_validation", "permission_denied"],
            "storage": ["disk_space"],
            "translation": ["translation_failed", "timeout"],
        }

        # Check if context has specific mappings
        if context in context_mappings:
            for error_key in context_mappings[context]:
                if error_key in ErrorHandler.SAFE_ERROR_MESSAGES:
                    return ErrorHandler.SAFE_ERROR_MESSAGES[error_key]

        # Check error type directly
        for safe_key, safe_message in ErrorHandler.SAFE_ERROR_MESSAGES.items():
            if error_type.lower().find(safe_key.split("_")[0].lower()) != -1:
                return safe_message

        # Fallback to unknown error
        return ErrorHandler.SAFE_ERROR_MESSAGES["unknown"]

    @staticmethod
    def _is_security_relevant(error_type: str) -> bool:
        """Check if error type is security-relevant."""
        security_relevant = [
            "PermissionError",
            "FileNotFoundError",
            "OSError",
            "ValidationError",
            "AuthenticationError",
            "AuthorizationError",
        ]
        return any(sec in error_type for sec in security_relevant)

    @staticmethod
    def _get_severity(error_type: str) -> ErrorSeverity:
        """Determine error severity based on type."""
        high_severity = [
            "PermissionError",
            "AuthenticationError",
            "AuthorizationError",
            "ValidationError",
            "ConfigurationError",
        ]

        medium_severity = [
            "ConnectionError",
            "TimeoutError",
            "RateLimitError",
            "PDFProcessingError",
            "TranslationError",
        ]

        if any(high in error_type for high in high_severity):
            return ErrorSeverity.HIGH
        elif any(med in error_type for med in medium_severity):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    @staticmethod
    def create_user_error(error_info: Dict[str, Any]) -> str:
        """Create user-friendly error message with context."""
        if not error_info.get("show_to_user", False):
            return ""

        base_message = error_info.get("user_message", "An error occurred")
        context = error_info.get("context", "")
        severity = error_info.get("severity", ErrorSeverity.MEDIUM.value)

        # Add contextual help based on error
        help_messages = {
            "api_authentication": "💡 Please check your API key in the configuration.",
            "api_rate_limit": "💡 Please wait a few moments before trying again.",
            "file_validation": "💡 Please upload a valid PDF file under 50MB.",
            "permission_denied": "💡 Please check file and directory permissions.",
            "disk_space": "💡 Please free up disk space and try again.",
            "pdf_processing": "💡 Ensure the PDF is not password-protected or corrupted.",
            "translation_failed": "💡 Try breaking the text into smaller sections.",
            "timeout": "💡 Check your internet connection and try again.",
        }

        help_text = help_messages.get(context, "")

        if help_text:
            return f"{base_message}\n\n{help_text}"

        return base_message

    @staticmethod
    def handle_translation_error(error: Exception, provider: str = "unknown") -> Dict[str, Any]:
        """Handle translation-specific errors."""
        error_map = {
            "google": {
                "google.generativeai.types.generationconfig": "configuration",
                "google.generativeai.types.generativemodel": "model_creation",
                "PermissionError": "permission",
                "RateLimitError": "rate_limit",
                "ConnectionError": "network",
            }
        }

        error_type = type(error).__name__
        context = error_map.get(provider, {}).get(error_type, "translation_failed")

        return ErrorHandler.handle_error(error, context=context, user_facing=True)


# Global error handler instance
error_handler = ErrorHandler()
