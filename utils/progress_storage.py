
"""
Progress storage utilities for saving and loading translation progress.
Allows resuming interrupted translations from the last completed paragraph.
Refactored to use SQLite for thread-safe concurrent access.
"""
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from config import config
from utils.logger_config import get_logger

logger = get_logger(__name__)

# Thread-local storage for SQLite connections
# SQLite connections cannot be shared data between threads in older versions, 
# and it's good practice to keep them separate anyway.
local_storage = threading.local()

def get_db_path() -> Path:
    """Get path to the SQLite database."""
    storage_dir = config.get_progress_storage_dir()
    return storage_dir / "translation_progress.db"

def get_connection():
    """Get a thread-local SQLite connection."""
    if not hasattr(local_storage, "connection"):
        db_path = get_db_path()
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect with timeout to handle locking
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception as e:
            logger.warning(f"Failed to set WAL mode: {e}")
            
        # Initialize schema for this connection
        # This ensures tables exist even if created by another process/thread
        try:
            # Jobs table stores metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    file_id TEXT PRIMARY KEY,
                    source_lang TEXT,
                    target_lang TEXT,
                    model_name TEXT,
                    total_paragraphs INTEGER,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            # Paragraphs table stores content
            conn.execute("""
                CREATE TABLE IF NOT EXISTS paragraphs (
                    file_id TEXT,
                    paragraph_idx INTEGER,
                    original_text TEXT,
                    translated_text TEXT,
                    PRIMARY KEY (file_id, paragraph_idx),
                    FOREIGN KEY (file_id) REFERENCES jobs (file_id)
                )
            """)
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize DB schema: {e}")
            
        local_storage.connection = conn
        
    return local_storage.connection

# init_db() was problematic if called at module level with recursion or timing issues.
# we removed it in favor of per-connection initialization.

def get_file_id(filename: str, size: int) -> str:
    """Generate unique file identifier."""
    file_id = f"{filename}_{size}"
    return file_id

def load_progress(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Load existing progress for a file.
    Reconstructs the dictionary format expected by the app.
    """
    conn = get_connection()
    try:
        # Get job metadata
        cursor = conn.execute("SELECT * FROM jobs WHERE file_id = ?", (file_id,))
        job = cursor.fetchone()
        
        if not job:
            return None
            
        # Get all paragraphs for this job
        cursor = conn.execute(
            "SELECT paragraph_idx, original_text, translated_text FROM paragraphs WHERE file_id = ? ORDER BY paragraph_idx", 
            (file_id,)
        )
        rows = cursor.fetchall()
        
        # Reconstruct format
        original_paragraphs = []
        translated_paragraphs = {}
        
        # We need to reconstruct original_paragraphs list with correct indices
        # Since we might have sparse data if something went wrong, we rely on updated_at/logic
        # But generally, we store all original paragraphs on creation.
        
        # Optimization: To avoid storing original text twice if not needed, 
        # we can reconstruct if we assume continuous indices. 
        # But strict reconstruction requires stored data.
        
        # Let's populate the dictionaries
        max_idx = -1
        temp_originals = {}
        
        for row in rows:
            idx = row['paragraph_idx']
            temp_originals[idx] = row['original_text']
            if row['translated_text']:
                translated_paragraphs[str(idx)] = row['translated_text']
            if idx > max_idx:
                max_idx = idx
        
        # Reconstruct list
        if job['total_paragraphs'] > 0:
            original_paragraphs = [temp_originals.get(i, "") for i in range(job['total_paragraphs'])]
        else:
            original_paragraphs = []

        return {
            'file_id': job['file_id'],
            'source_lang': job['source_lang'],
            'target_lang': job['target_lang'],
            'model_name': job['model_name'],
            'total_paragraphs': job['total_paragraphs'],
            'original_paragraphs': original_paragraphs,
            'translated_paragraphs': translated_paragraphs,
            'completed_paragraphs': len(translated_paragraphs),
            'updated_at': job['updated_at']
        }
        
    except Exception as e:
        logger.error(f"Error loading progress for {file_id}: {e}", exc_info=True)
        return None

def update_progress_paragraph(
    file_id: str, 
    paragraph_idx: int, 
    translated_text: str,
    original_paragraphs: list,
    source_lang: str,
    target_lang: str,
    model_name: str
) -> bool:
    """
    Update progress with a newly translated paragraph.
    Uses SQLite upsert for efficient concurrent writes.
    """
    conn = get_connection()
    try:
        now = datetime.now().isoformat()
        
        # 1. Ensure Job exists (or update timestamp)
        # We use INSERT OR IGNORE for creation, then UPDATE for timestamp.
        # Or an UPSERT if supported. Standard SQLite UPSERT:
        conn.execute("""
            INSERT INTO jobs (file_id, source_lang, target_lang, model_name, total_paragraphs, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_id) DO UPDATE SET updated_at=excluded.updated_at
        """, (file_id, source_lang, target_lang, model_name, len(original_paragraphs), now, now))
        
        # 2. Insert/Update Paragraph
        # Note: We store original text here. It might be redundant to update it every time, 
        # but it ensures the DB is self-contained.
        original_text = original_paragraphs[paragraph_idx] if paragraph_idx < len(original_paragraphs) else ""
        
        conn.execute("""
            INSERT INTO paragraphs (file_id, paragraph_idx, original_text, translated_text)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(file_id, paragraph_idx) DO UPDATE SET translated_text=excluded.translated_text
        """, (file_id, paragraph_idx, original_text, translated_text))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Failed to update progress for {file_id} para {paragraph_idx}: {e}")
        return False

def delete_progress(file_id: str, reason: str = "translation completed") -> bool:
    """Delete progress for a file_id."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM paragraphs WHERE file_id = ?", (file_id,))
        conn.execute("DELETE FROM jobs WHERE file_id = ?", (file_id,))
        conn.commit()
        logger.info(f"Progress deleted: file_id={file_id}, reason={reason}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete progress for {file_id}: {e}")
        return False

def get_translated_text_from_progress(progress_data: Dict[str, Any]) -> str:
    """Reconstruct translated text from progress data object."""
    # This logic remains same as it works on the Dict we return from load_progress
    translated_paragraphs = progress_data.get('translated_paragraphs', {})
    total_paragraphs = progress_data.get('total_paragraphs', 0)
    
    result_paragraphs = []
    for idx in range(total_paragraphs):
        if str(idx) in translated_paragraphs:
            result_paragraphs.append(translated_paragraphs[str(idx)])
    
    return '\n\n'.join(result_paragraphs)
