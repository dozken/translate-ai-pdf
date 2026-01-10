"""
Configuration management for LLM Translation Cost Calculator.
Centralizes all environment variable access and provides defaults.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # API Keys (strip whitespace to avoid issues)
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY", "").strip() or None
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "").strip() or None
    DEEPL_API_KEY: Optional[str] = os.getenv("DEEPL_API_KEY", "").strip() or None
    
    # Translation Settings
    SOURCE_LANGUAGE: str = os.getenv("SOURCE_LANGUAGE", "Arabic")
    TARGET_LANGUAGE: str = os.getenv("TARGET_LANGUAGE", "Russian")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-pro")
    
    # Performance Settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TRANSLATION_DELAY_SECONDS: float = float(os.getenv("TRANSLATION_DELAY_SECONDS", "0.5"))
    ENABLE_STREAMING: bool = os.getenv("ENABLE_STREAMING", "true").lower() in ("true", "1", "yes")
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "5"))
    
    # PDF Output Settings
    PDF_OUTPUT_DIR: Optional[str] = os.getenv("PDF_OUTPUT_DIR")
    
    # Progress Storage Settings
    PROGRESS_STORAGE_DIR: Optional[str] = os.getenv("PROGRESS_STORAGE_DIR")
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    LOG_DIR: Optional[str] = os.getenv("LOG_DIR")  # Directory for log files
    LOG_CONSOLE_OUTPUT: bool = os.getenv("LOG_CONSOLE_OUTPUT", "true").lower() in ("true", "1", "yes")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB default
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # Number of backup log files
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate configuration and return list of missing required settings.
        
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        
        # Note: API keys are only required when using specific providers
        # This is handled at runtime in the translation functions
        
        if cls.MAX_RETRIES < 1:
            errors.append("MAX_RETRIES must be at least 1")
        
        if cls.TRANSLATION_DELAY_SECONDS < 0:
            errors.append("TRANSLATION_DELAY_SECONDS must be non-negative")
        
        return errors
    
    @classmethod
    def get_pdf_output_dir(cls) -> Path:
        """
        Get the PDF output directory, creating it if necessary.
        
        Returns:
            Path object for the output directory
        """
        if cls.PDF_OUTPUT_DIR:
            output_dir = Path(cls.PDF_OUTPUT_DIR)
        else:
            import tempfile
            output_dir = Path(tempfile.gettempdir())
        
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    @classmethod
    def get_progress_storage_dir(cls) -> Path:
        """
        Get the progress storage directory, creating it if necessary.
        
        Returns:
            Path object for the progress storage directory
        """
        if cls.PROGRESS_STORAGE_DIR:
            storage_dir = Path(cls.PROGRESS_STORAGE_DIR)
        else:
            # Default to ./progress/ directory in current working directory
            storage_dir = Path.cwd() / "progress"
        
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir


# Create a singleton instance
config = Config()
