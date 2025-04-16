"""
Session History Module

Handles storing and retrieving session history, including:
- Player input and DM output
- Important choices and decisions
- Major events (combat, character death, NPC betrayal, etc.)
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from enum import Enum
from pydantic import BaseModel, Field

class EventType(str, Enum):
    """Types of major events that can occur in a session"""
    COMBAT = "combat"
    CHARACTER_DEATH = "character_death"
    NPC_BETRAYAL = "npc_betrayal"
    QUEST_STARTED = "quest_started"
    QUEST_COMPLETED = "quest_completed"
    LOCATION_DISCOVERED = "location_discovered"
    ITEM_ACQUIRED = "item_acquired"
    LEVEL_UP = "level_up"
    BOSS_DEFEATED = "boss_defeated"
    NARRATIVE_MILESTONE = "narrative_milestone"
    PLAYER_CHOICE = "player_choice"
    CUSTOM = "custom"

class MessageType(str, Enum):
    """Types of messages in a session"""
    PLAYER = "player"
    DM = "dm"
    SYSTEM = "system"
    COMBAT = "combat"

class HistoryMessage(BaseModel):
    """Model for a message in the session history"""
    id: str
    session_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = {}

class MajorEvent(BaseModel):
    """Model for a major event in the session history"""
    id: str
    session_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event_type: EventType
    description: str
    related_entities: List[str] = []  # IDs of characters, NPCs, locations, etc.
    metadata: Dict[str, Any] = {}

class SessionInfo(BaseModel):
    """Model for session metadata"""
    id: str
    campaign_id: str
    name: str
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    player_characters: List[str] = []
    starting_location: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []

class SessionHistory:
    """Manages session history for a campaign"""
    
    def __init__(self, db_path: str = "./saves/history.db"):
        """Initialize the session history manager with a database path"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database for storing session history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                name TEXT,
                start_time TEXT,
                end_time TEXT,
                player_characters TEXT,
                starting_location TEXT,
                summary TEXT,
                tags TEXT,
                session_data TEXT
            )
        """)
        
        # Create table for messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                message_type TEXT,
                content TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Create table for major events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                event_type TEXT,
                description TEXT,
                related_entities TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Create indices for faster querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_campaign ON sessions (campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_session ON messages (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_session ON events (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events (event_type)")
        
        conn.commit()
        conn.close()
    
    def create_session(self, session: SessionInfo) -> None:
        """
        Create a new session
        
        Args:
            session: SessionInfo object with session metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serialize player characters and tags
        player_characters = ",".join(session.player_characters)
        tags = ",".join(session.tags)
        
        # Serialize the session data
        session_data = session.model_dump_json()
        
        cursor.execute("""
            INSERT INTO sessions
            (id, campaign_id, name, start_time, end_time, player_characters,
             starting_location, summary, tags, session_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.id, session.campaign_id, session.name, session.start_time,
            session.end_time, player_characters, session.starting_location,
            session.summary, tags, session_data
        ))
        
        conn.commit()
        conn.close()
    
    def end_session(self, session_id: str, summary: Optional[str] = None) -> None:
        """
        End a session by setting its end time and optional summary
        
        Args:
            session_id: ID of the session to end
            summary: Optional summary of the session
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_time = datetime.now().isoformat()
        
        # Update the session
        if summary:
            cursor.execute(
                "UPDATE sessions SET end_time = ?, summary = ? WHERE id = ?",
                (end_time, summary, session_id)
            )
        else:
            cursor.execute(
                "UPDATE sessions SET end_time = ? WHERE id = ?",
                (end_time, session_id)
            )
        
        # Also update the session data JSON
        cursor.execute(
            "SELECT session_data FROM sessions WHERE id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        if result:
            session_data = json.loads(result[0])
            session_data["end_time"] = end_time
            if summary:
                session_data["summary"] = summary
            
            cursor.execute(
                "UPDATE sessions SET session_data = ? WHERE id = ?",
                (json.dumps(session_data), session_id)
            )
        
        conn.commit()
        conn.close()
    
    def add_message(self, message: HistoryMessage) -> None:
        """
        Add a message to the session history
        
        Args:
            message: HistoryMessage to add
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serialize the metadata
        metadata_json = json.dumps(message.metadata)
        
        cursor.execute("""
            INSERT INTO messages
            (id, session_id, timestamp, message_type, content, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message.id, message.session_id, message.timestamp,
            message.message_type.value, message.content, metadata_json
        ))
        
        conn.commit()
        conn.close()
    
    def add_event(self, event: MajorEvent) -> None:
        """
        Add a major event to the session history
        
        Args:
            event: MajorEvent to add
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serialize related entities and metadata
        related_entities = ",".join(event.related_entities)
        metadata_json = json.dumps(event.metadata)
        
        cursor.execute("""
            INSERT INTO events
            (id, session_id, timestamp, event_type, description, related_entities, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id, event.session_id, event.timestamp,
            event.event_type.value, event.description, related_entities, metadata_json
        ))
        
        conn.commit()
        conn.close()
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session info by ID
        
        Args:
            session_id: ID of the session
            
        Returns:
            SessionInfo object, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT session_data FROM sessions WHERE id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        session_data = json.loads(result[0])
        return SessionInfo.model_validate(session_data)
    
    def get_campaign_sessions(self, campaign_id: str) -> List[SessionInfo]:
        """
        Get all sessions for a campaign
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            List of SessionInfo objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT session_data FROM sessions WHERE campaign_id = ? ORDER BY start_time",
            (campaign_id,)
        )
        
        sessions = []
        for row in cursor.fetchall():
            session_data = json.loads(row[0])
            sessions.append(SessionInfo.model_validate(session_data))
        
        conn.close()
        return sessions
    
    def get_session_messages(self, session_id: str, 
                            message_types: Optional[List[MessageType]] = None,
                            limit: Optional[int] = None) -> List[HistoryMessage]:
        """
        Get messages for a session, optionally filtered by type
        
        Args:
            session_id: ID of the session
            message_types: Optional list of message types to filter by
            limit: Optional maximum number of messages to return
            
        Returns:
            List of HistoryMessage objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, session_id, timestamp, message_type, content, metadata FROM messages WHERE session_id = ?"
        params = [session_id]
        
        if message_types:
            type_values = [t.value for t in message_types]
            placeholders = ",".join(["?"] * len(type_values))
            query += f" AND message_type IN ({placeholders})"
            params.extend(type_values)
        
        query += " ORDER BY timestamp"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        
        messages = []
        for row in cursor.fetchall():
            msg_id, sess_id, timestamp, msg_type, content, metadata_json = row
            metadata = json.loads(metadata_json)
            
            messages.append(HistoryMessage(
                id=msg_id,
                session_id=sess_id,
                timestamp=timestamp,
                message_type=MessageType(msg_type),
                content=content,
                metadata=metadata
            ))
        
        conn.close()
        return messages
    
    def get_session_events(self, session_id: str,
                          event_types: Optional[List[EventType]] = None) -> List[MajorEvent]:
        """
        Get major events for a session, optionally filtered by type
        
        Args:
            session_id: ID of the session
            event_types: Optional list of event types to filter by
            
        Returns:
            List of MajorEvent objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, session_id, timestamp, event_type, description, related_entities, metadata 
            FROM events WHERE session_id = ?
        """
        params = [session_id]
        
        if event_types:
            type_values = [t.value for t in event_types]
            placeholders = ",".join(["?"] * len(type_values))
            query += f" AND event_type IN ({placeholders})"
            params.extend(type_values)
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            evt_id, sess_id, timestamp, evt_type, description, related_entities_str, metadata_json = row
            
            related_entities = related_entities_str.split(",") if related_entities_str else []
            metadata = json.loads(metadata_json)
            
            events.append(MajorEvent(
                id=evt_id,
                session_id=sess_id,
                timestamp=timestamp,
                event_type=EventType(evt_type),
                description=description,
                related_entities=related_entities,
                metadata=metadata
            ))
        
        conn.close()
        return events
    
    def get_campaign_events(self, campaign_id: str,
                           event_types: Optional[List[EventType]] = None) -> List[MajorEvent]:
        """
        Get all major events for a campaign, optionally filtered by type
        
        Args:
            campaign_id: ID of the campaign
            event_types: Optional list of event types to filter by
            
        Returns:
            List of MajorEvent objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First get all session IDs for the campaign
        cursor.execute(
            "SELECT id FROM sessions WHERE campaign_id = ?",
            (campaign_id,)
        )
        
        session_ids = [row[0] for row in cursor.fetchall()]
        if not session_ids:
            conn.close()
            return []
        
        # Now get events for these sessions
        placeholders = ",".join(["?"] * len(session_ids))
        query = f"""
            SELECT id, session_id, timestamp, event_type, description, related_entities, metadata 
            FROM events WHERE session_id IN ({placeholders})
        """
        params = session_ids
        
        if event_types:
            type_values = [t.value for t in event_types]
            type_placeholders = ",".join(["?"] * len(type_values))
            query += f" AND event_type IN ({type_placeholders})"
            params.extend(type_values)
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            evt_id, sess_id, timestamp, evt_type, description, related_entities_str, metadata_json = row
            
            related_entities = related_entities_str.split(",") if related_entities_str else []
            metadata = json.loads(metadata_json)
            
            events.append(MajorEvent(
                id=evt_id,
                session_id=sess_id,
                timestamp=timestamp,
                event_type=EventType(evt_type),
                description=description,
                related_entities=related_entities,
                metadata=metadata
            ))
        
        conn.close()
        return events
    
    def get_entity_history(self, entity_id: str) -> List[MajorEvent]:
        """
        Get all events related to a specific entity (character, NPC, location, etc.)
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            List of MajorEvent objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, session_id, timestamp, event_type, description, related_entities, metadata FROM events WHERE related_entities LIKE ?",
            (f"%{entity_id}%",)
        )
        
        events = []
        for row in cursor.fetchall():
            evt_id, sess_id, timestamp, evt_type, description, related_entities_str, metadata_json = row
            
            related_entities = related_entities_str.split(",") if related_entities_str else []
            metadata = json.loads(metadata_json)
            
            # Only include if the entity is actually in the related entities
            # (This handles cases where the entity ID is a substring of another ID)
            if entity_id in related_entities:
                events.append(MajorEvent(
                    id=evt_id,
                    session_id=sess_id,
                    timestamp=timestamp,
                    event_type=EventType(evt_type),
                    description=description,
                    related_entities=related_entities,
                    metadata=metadata
                ))
        
        conn.close()
        return events
    
    def generate_session_summary(self, session_id: str) -> str:
        """
        Generate a summary of a session based on its messages and events
        
        Args:
            session_id: ID of the session
            
        Returns:
            A summary string
        """
        # Get session info
        session = self.get_session(session_id)
        if not session:
            return "Session not found"
        
        # Get major events
        events = self.get_session_events(session_id)
        
        # Get a sample of messages (first, last, and some in between)
        messages = self.get_session_messages(session_id)
        
        summary_parts = [f"Session: {session.name}"]
        summary_parts.append(f"Date: {session.start_time[:10]}")
        
        if session.player_characters:
            summary_parts.append(f"Characters: {', '.join(session.player_characters)}")
        
        if events:
            summary_parts.append("\nMajor Events:")
            for event in events:
                summary_parts.append(f"- {event.event_type.value.replace('_', ' ').title()}: {event.description}")
        
        if messages:
            # Add a brief dialogue sample
            summary_parts.append("\nDialogue Highlights:")
            
            # Add first message
            first_msg = messages[0]
            summary_parts.append(f"{first_msg.message_type.value.upper()}: {first_msg.content[:100]}...")
            
            # Add a middle message if there are enough
            if len(messages) > 5:
                mid_msg = messages[len(messages) // 2]
                summary_parts.append(f"{mid_msg.message_type.value.upper()}: {mid_msg.content[:100]}...")
            
            # Add last message
            last_msg = messages[-1]
            summary_parts.append(f"{last_msg.message_type.value.upper()}: {last_msg.content[:100]}...")
        
        return "\n".join(summary_parts)
    
    def export_session_log(self, session_id: str, output_path: str) -> None:
        """
        Export a session log to a text file
        
        Args:
            session_id: ID of the session
            output_path: Path to save the log file
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        messages = self.get_session_messages(session_id)
        events = self.get_session_events(session_id)
        
        with open(output_path, 'w') as f:
            # Write header
            f.write(f"Session: {session.name}\n")
            f.write(f"Date: {session.start_time[:10]}\n")
            f.write(f"Campaign: {session.campaign_id}\n")
            if session.player_characters:
                f.write(f"Characters: {', '.join(session.player_characters)}\n")
            f.write("\n" + "="*50 + "\n\n")
            
            # Merge messages and events into a chronological log
            log_entries = []
            
            for msg in messages:
                log_entries.append({
                    'timestamp': msg.timestamp,
                    'type': 'message',
                    'content': f"{msg.message_type.value.upper()}: {msg.content}"
                })
            
            for evt in events:
                log_entries.append({
                    'timestamp': evt.timestamp,
                    'type': 'event',
                    'content': f"[EVENT - {evt.event_type.value.replace('_', ' ').upper()}] {evt.description}"
                })
            
            # Sort by timestamp
            log_entries.sort(key=lambda x: x['timestamp'])
            
            # Write log entries
            for entry in log_entries:
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                f.write(f"[{timestamp}] {entry['content']}\n\n")
            
            # Write footer
            f.write("\n" + "="*50 + "\n\n")
            if session.summary:
                f.write(f"Summary: {session.summary}\n")