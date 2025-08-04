# app/database.py

import sqlite3
import json
import logging
import os
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Database file path - use absolute path to avoid issues
DB_PATH = os.path.join(os.path.dirname(__file__), "user_history.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database by creating the conversation_history table
    if it does not already exist. This should be called on application startup.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                turn INTEGER NOT NULL,
                user_query TEXT NOT NULL,
                filters_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("Database initialized and 'conversation_history' table is ready.")

def add_turn_to_history(session_id: str, user_query: str, filters_state: Dict[str, Any]):
    """
    Adds a new turn to a session's conversation history.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get the next turn number
        cursor.execute("SELECT COALESCE(MAX(turn), 0) + 1 FROM conversation_history WHERE session_id = ?", (session_id,))
        next_turn = cursor.fetchone()[0]

        # Convert the filters dictionary to a JSON string for storage
        filters_json = json.dumps(filters_state)
        
        cursor.execute("""
            INSERT INTO conversation_history (session_id, turn, user_query, filters_json)
            VALUES (?, ?, ?, ?)
        """, (session_id, next_turn, user_query, filters_json))
        
        conn.commit()
        logger.info(f"Saved turn {next_turn} for session {session_id}.")

def get_history_for_session(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves the entire conversation history for a given session,
    ordered by the turn number.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, turn, user_query, filters_json, created_at
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY turn ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        # Convert sqlite3.Row objects to standard dictionaries
        history = [dict(row) for row in rows]
        logger.info(f"Retrieved {len(history)} turns for session {session_id}.")
        return history