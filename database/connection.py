import sqlite3
import json
import os
from typing import Any, Dict, Optional
from contextlib import contextmanager

DATABASE_PATH = "rogr_trustfeed.db"

def get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        # Create trustfeed_entries table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trustfeed_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_summary TEXT NOT NULL,
                trust_score REAL,
                grade TEXT,
                source_url TEXT,
                source_domain TEXT,
                claims_analyzed INTEGER DEFAULT 0,
                scan_mode TEXT,
                tags TEXT, -- JSON array
                categories TEXT, -- JSON array
                full_capsule_data TEXT, -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better query performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trust_score ON trustfeed_entries(trust_score)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source_domain ON trustfeed_entries(source_domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON trustfeed_entries(created_at)")

def json_to_str(data: Any) -> str:
    """Convert Python data to JSON string for database storage."""
    if data is None:
        return None
    return json.dumps(data)

def str_to_json(data: str) -> Any:
    """Convert JSON string from database to Python data."""
    if data is None or data == "":
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None

def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a SELECT query and return results."""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def execute_insert(query: str, params: tuple = ()) -> int:
    """Execute an INSERT query and return the last row ID."""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.lastrowid

def execute_update(query: str, params: tuple = ()) -> int:
    """Execute an UPDATE/DELETE query and return affected row count."""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.rowcount