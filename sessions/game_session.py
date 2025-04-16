"""
Game Session Module

Handles the current game session, including scene context, history, and state.
"""

import json
import os
import time
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime

class GameSession:
    """
    Manages the current game session, including scene context, history, and state.
    """
    
    def __init__(self, 
                session_id: Optional[str] = None, 
                character: Any = None,
                db_path: str = "sessions/game_sessions.db"):
        """
        Initialize a game session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            character: Optional character object
            db_path: Path to the SQLite database for session storage
        """
        self.session_id = session_id or f"session_{int(time.time())}"
        self.character = character
        self.db_path = db_path
        self.scene_context = "You stand at the entrance of a dark, mysterious cave."
        self.history = []
        self.companions = []
        self.current_location = "Cave Entrance"
        self.started_at = datetime.now()
        self.last_updated = self.started_at
        
        # Initialize the database if it doesn't exist
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database for session storage."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            character_name TEXT,
            current_location TEXT,
            started_at TEXT,
            last_updated TEXT
        )
        ''')
        
        # Create history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TEXT,
            player_input TEXT,
            dm_response TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_to_history(self, player_input: str, dm_response: str) -> None:
        """
        Add an exchange to the session history.
        
        Args:
            player_input: The player's input text
            dm_response: The DM's response text
        """
        timestamp = datetime.now()
        self.last_updated = timestamp
        
        # Add to in-memory history
        self.history.append({
            "timestamp": timestamp.isoformat(),
            "player_input": player_input,
            "dm_response": dm_response
        })
        
        # Add to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO history (session_id, timestamp, player_input, dm_response)
        VALUES (?, ?, ?, ?)
        ''', (self.session_id, timestamp.isoformat(), player_input, dm_response))
        
        # Update session last_updated
        cursor.execute('''
        UPDATE sessions SET last_updated = ? WHERE session_id = ?
        ''', (timestamp.isoformat(), self.session_id))
        
        conn.commit()
        conn.close()
    
    def update_scene_context(self, new_context: str) -> None:
        """
        Update the current scene context.
        
        Args:
            new_context: The new scene context
        """
        self.scene_context = new_context
        self.last_updated = datetime.now()
    
    def update_location(self, location: str) -> None:
        """
        Update the current location.
        
        Args:
            location: The new location name
        """
        self.current_location = location
        self.last_updated = datetime.now()
        
        # Update in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE sessions SET current_location = ?, last_updated = ? WHERE session_id = ?
        ''', (location, self.last_updated.isoformat(), self.session_id))
        
        conn.commit()
        conn.close()
    
    def save(self) -> None:
        """Save the current session state to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if session exists
        cursor.execute('SELECT 1 FROM sessions WHERE session_id = ?', (self.session_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing session
            cursor.execute('''
            UPDATE sessions SET 
                character_name = ?,
                current_location = ?,
                last_updated = ?
            WHERE session_id = ?
            ''', (
                self.character.name if self.character else None,
                self.current_location,
                self.last_updated.isoformat(),
                self.session_id
            ))
        else:
            # Insert new session
            cursor.execute('''
            INSERT INTO sessions (session_id, character_name, current_location, started_at, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                self.session_id,
                self.character.name if self.character else None,
                self.current_location,
                self.started_at.isoformat(),
                self.last_updated.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    @classmethod
    def load(cls, session_id: str, db_path: str = "sessions/game_sessions.db") -> 'GameSession':
        """
        Load a session from the database.
        
        Args:
            session_id: The session ID to load
            db_path: Path to the SQLite database
            
        Returns:
            GameSession object
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Session database not found: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for named columns
        cursor = conn.cursor()
        
        # Get session data
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session_data = cursor.fetchone()
        
        if not session_data:
            conn.close()
            raise ValueError(f"Session not found: {session_id}")
        
        # Create session object
        session = cls(session_id=session_id, db_path=db_path)
        session.current_location = session_data['current_location']
        session.started_at = datetime.fromisoformat(session_data['started_at'])
        session.last_updated = datetime.fromisoformat(session_data['last_updated'])
        
        # Load history
        cursor.execute('''
        SELECT timestamp, player_input, dm_response FROM history 
        WHERE session_id = ? ORDER BY timestamp
        ''', (session_id,))
        
        history_data = cursor.fetchall()
        session.history = [
            {
                "timestamp": row['timestamp'],
                "player_input": row['player_input'],
                "dm_response": row['dm_response']
            }
            for row in history_data
        ]
        
        conn.close()
        return session
    
    @classmethod
    def list_sessions(cls, db_path: str = "sessions/game_sessions.db") -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            List of session dictionaries
        """
        if not os.path.exists(db_path):
            return []
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT session_id, character_name, current_location, started_at, last_updated 
        FROM sessions ORDER BY last_updated DESC
        ''')
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sessions
    
    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent history entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent history entries
        """
        return self.history[-limit:] if self.history else []
    
    def get_formatted_history_for_llm(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get formatted history for the LLM.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of formatted history entries for the LLM
        """
        recent_history = self.get_recent_history(limit)
        formatted_history = []
        
        for entry in recent_history:
            formatted_history.append({
                "role": "user",
                "content": entry["player_input"]
            })
            formatted_history.append({
                "role": "assistant",
                "content": entry["dm_response"]
            })
        
        return formatted_history

# TODO: Add support for saving/loading the full game state including character
# TODO: Add support for multiple characters in a session
# TODO: Add support for tracking game events and quest progress