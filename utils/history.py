"""
utils/history.py
----------------
SQLite-backed prompt history and feedback persistence.
Database: data/chat_history.db
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Config

logger = logging.getLogger(__name__)

DB_PATH = Config.DATA_DIR / "chat_history.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create the prompt_history table if it does not exist."""
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_history (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id            TEXT NOT NULL,
                question              TEXT NOT NULL,
                answer                TEXT NOT NULL,
                sources               TEXT,
                response_time_seconds REAL,
                total_tokens          INTEGER,
                feedback              TEXT DEFAULT NULL,
                timestamp             TEXT NOT NULL
            )
        """)
        conn.commit()
        logger.info("Prompt history database initialized at %s", DB_PATH)
    finally:
        conn.close()


def save_turn(
    session_id: str,
    question: str,
    answer: str,
    sources: Optional[List[Dict[str, Any]]] = None,
    response_time: Optional[float] = None,
    total_tokens: Optional[int] = None,
) -> int:
    """Insert a conversation turn and return the inserted row id."""
    sources_json = json.dumps(sources) if sources else None
    timestamp = datetime.now().isoformat(timespec="seconds")
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO prompt_history
                (session_id, question, answer, sources,
                 response_time_seconds, total_tokens, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, question, answer, sources_json,
             response_time, total_tokens, timestamp),
        )
        conn.commit()
        row_id = cursor.lastrowid
        logger.info("Saved turn id=%d for session %s", row_id, session_id)
        return row_id
    finally:
        conn.close()


def get_session_history(session_id: str) -> List[Dict[str, Any]]:
    """Return all turns for a given session as a list of dicts."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM prompt_history WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_sessions() -> List[Dict[str, Any]]:
    """Return distinct session_ids with turn count and last timestamp."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT session_id,
                   COUNT(*) AS turn_count,
                   MAX(timestamp) AS last_timestamp
            FROM prompt_history
            GROUP BY session_id
            ORDER BY last_timestamp DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_recent_queries(limit: int = 20) -> List[Dict[str, Any]]:
    """Return the most recent N turns across all sessions."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM prompt_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_total_questions() -> int:
    """Return the total count of all rows in prompt_history."""
    conn = _get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM prompt_history").fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def delete_session(session_id: str) -> None:
    """Delete all rows for a given session."""
    conn = _get_connection()
    try:
        conn.execute(
            "DELETE FROM prompt_history WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()
        logger.info("Deleted session %s", session_id)
    finally:
        conn.close()


def save_feedback(turn_id: int, feedback: str) -> None:
    """Update the feedback column for a given turn id."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE prompt_history SET feedback = ? WHERE id = ?",
            (feedback, turn_id),
        )
        conn.commit()
        logger.info("Saved feedback '%s' for turn id=%d", feedback, turn_id)
    finally:
        conn.close()


# Initialize the database on import
init_db()
