"""
Centralized logging configuration for LLM Translation Cost Calculator.
Provides structured logging with rotation, multiple handlers, and better formatting.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from config import config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    console_output: Optional[bool] = None
) -> logging.Logger:
    """
    Set up application-wide logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name (if None, uses default from config or 'app.log')
        log_dir: Directory for log files (if None, uses current directory or config)
        max_bytes: Maximum size of log file before rotation (default: from config or 10MB)
        backup_count: Number of backup log files to keep (default: from config or 5)
        console_output: Whether to output logs to console (default: from config or True)
        
    Returns:
        Root logger instance
    """
    # Get configuration with fallbacks
    level = log_level or config.LOG_LEVEL
    log_file_name = log_file or config.LOG_FILE or "app.log"
    max_bytes = max_bytes if max_bytes is not None else config.LOG_MAX_BYTES
    backup_count = backup_count if backup_count is not None else config.LOG_BACKUP_COUNT
    console_output = console_output if console_output is not None else config.LOG_CONSOLE_OUTPUT
    
    # Determine log directory
    if log_dir:
        log_dir_path = Path(log_dir)
    elif config.LOG_DIR:
        log_dir_path = Path(config.LOG_DIR)
    elif config.LOG_FILE and Path(config.LOG_FILE).parent.exists():
        log_dir_path = Path(config.LOG_FILE).parent
    else:
        log_dir_path = Path.cwd() / "logs"
    
    # Create log directory if it doesn't exist
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Full log file path
    if Path(log_file_name).is_absolute():
        log_file_path = Path(log_file_name)
    else:
        log_file_path = log_dir_path / log_file_name
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler (for development/debugging)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # If we can't write to the log file, at least log to console
        root_logger.warning(f"Could not create log file at {log_file_path}: {e}. Logging to console only.")
    
    # Error file handler (separate file for errors and above)
    error_log_path = log_dir_path / f"error_{log_file_path.stem}{log_file_path.suffix}"
    try:
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    except (PermissionError, OSError) as e:
        root_logger.warning(f"Could not create error log file at {error_log_path}: {e}")
    
    # Log initial configuration
    root_logger.info("=" * 80)
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log level: {level} ({numeric_level})")
    root_logger.info(f"Log file: {log_file_path}")
    root_logger.info(f"Error log file: {error_log_path}")
    root_logger.info(f"Console output: {console_output}")
    root_logger.info("=" * 80)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Performance logging decorator
def log_performance(logger: logging.Logger):
    """
    Decorator to log function execution time.
    
    Usage:
        @log_performance(logger)
        def my_function():
            ...
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Starting {func.__name__}")
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"Completed {func.__name__} in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed {func.__name__} after {elapsed:.3f}s: {e}", exc_info=True)
                raise
        return wrapper
    return decorator
