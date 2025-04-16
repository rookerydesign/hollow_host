"""
Lore Manager Module

Handles creation, storage, and retrieval of world lore elements:
- Factions
- NPCs
- Places
- Events
- Player-known facts
- Journal entries
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from pydantic import BaseModel, Field
from enum import Enum

class LoreType(str, Enum):
    """Types of lore elements"""
    FACTION = "faction"
    NPC = "npc"
    PLACE = "place"
    EVENT = "event"
    FACT = "fact"
    JOURNAL = "journal"

class LoreElement(BaseModel):
    """Base model for all lore elements"""
    id: str
    name: str
    description: str
    lore_type: LoreType
    tags: List[str] = []
    discovered: bool = False
    discovery_timestamp: Optional[str] = None
    related_elements: List[str] = []  # IDs of related lore elements
    metadata: Dict[str, Any] = {}

class Faction(LoreElement):
    """Model for faction lore elements"""
    leader: Optional[str] = None  # ID of NPC who leads the faction
    members: List[str] = []  # IDs of NPCs who are members
    alignment: str = "neutral"
    goals: List[str] = []
    territories: List[str] = []  # IDs of places controlled by faction
    relationships: Dict[str, str] = {}  # faction_id -> relationship (ally, enemy, neutral)

class NPC(LoreElement):
    """Model for NPC lore elements"""
    faction_id: Optional[str] = None
    location_id: Optional[str] = None
    role: str = ""
    personality: List[str] = []
    appearance: str = ""
    motivations: List[str] = []
    secrets: List[str] = []
    is_alive: bool = True

class Place(LoreElement):
    """Model for place lore elements"""
    region: str = ""
    controlling_faction: Optional[str] = None
    notable_npcs: List[str] = []
    points_of_interest: List[str] = []
    dangers: List[str] = []
    resources: List[str] = []
    visited: bool = False

class Event(LoreElement):
    """Model for event lore elements"""
    date: str = ""
    location_ids: List[str] = []
    participants: List[str] = []  # IDs of NPCs or factions
    consequences: List[str] = []
    player_involved: bool = False

class Fact(LoreElement):
    """Model for fact lore elements"""
    truth_value: bool = True  # Whether the fact is actually true
    source: Optional[str] = None  # ID of NPC or faction that provided this fact
    confidence: int = 100  # 0-100 scale of how confident the player should be

class JournalEntry(LoreElement):
    """Model for journal entry lore elements"""
    entry_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    location_id: Optional[str] = None
    characters_present: List[str] = []
    narrative_text: str = ""
    player_notes: str = ""

class LoreManager:
    """Manages lore elements for a campaign"""
    
    def __init__(self, db_path: str = "./saves/lore.db"):
        """Initialize the lore manager with a database path"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database for storing lore elements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for lore elements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lore_elements (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                name TEXT,
                description TEXT,
                lore_type TEXT,
                tags TEXT,
                discovered INTEGER,
                discovery_timestamp TEXT,
                related_elements TEXT,
                metadata TEXT,
                element_data TEXT
            )
        """)
        
        # Create index for faster querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaign_type ON lore_elements (campaign_id, lore_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON lore_elements (tags)")
        
        conn.commit()
        conn.close()
    
    def _serialize_tags(self, tags: List[str]) -> str:
        """Serialize tags list to string for storage"""
        return ",".join(tags)
    
    def _deserialize_tags(self, tags_str: str) -> List[str]:
        """Deserialize tags string to list"""
        return tags_str.split(",") if tags_str else []
    
    def _serialize_related(self, related: List[str]) -> str:
        """Serialize related elements list to string for storage"""
        return ",".join(related)
    
    def _deserialize_related(self, related_str: str) -> List[str]:
        """Deserialize related elements string to list"""
        return related_str.split(",") if related_str else []
    
    def add_lore_element(self, campaign_id: str, element: LoreElement) -> None:
        """
        Add or update a lore element
        
        Args:
            campaign_id: ID of the campaign
            element: LoreElement to add or update
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Set discovery timestamp if discovered and not already set
        if element.discovered and not element.discovery_timestamp:
            element.discovery_timestamp = datetime.now().isoformat()
        
        # Serialize the element data
        element_data = element.model_dump_json()
        
        # Check if element already exists
        cursor.execute(
            "SELECT id FROM lore_elements WHERE id = ? AND campaign_id = ?",
            (element.id, campaign_id)
        )
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update existing element
            cursor.execute("""
                UPDATE lore_elements
                SET name = ?, description = ?, lore_type = ?, tags = ?,
                    discovered = ?, discovery_timestamp = ?, related_elements = ?,
                    metadata = ?, element_data = ?
                WHERE id = ? AND campaign_id = ?
            """, (
                element.name, element.description, element.lore_type.value,
                self._serialize_tags(element.tags), int(element.discovered),
                element.discovery_timestamp, self._serialize_related(element.related_elements),
                json.dumps(element.metadata), element_data,
                element.id, campaign_id
            ))
        else:
            # Insert new element
            cursor.execute("""
                INSERT INTO lore_elements
                (id, campaign_id, name, description, lore_type, tags,
                 discovered, discovery_timestamp, related_elements, metadata, element_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                element.id, campaign_id, element.name, element.description,
                element.lore_type.value, self._serialize_tags(element.tags),
                int(element.discovered), element.discovery_timestamp,
                self._serialize_related(element.related_elements),
                json.dumps(element.metadata), element_data
            ))
        
        conn.commit()
        conn.close()
    
    def get_lore_element(self, campaign_id: str, element_id: str) -> Optional[LoreElement]:
        """
        Get a lore element by ID
        
        Args:
            campaign_id: ID of the campaign
            element_id: ID of the lore element
            
        Returns:
            The lore element, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT lore_type, element_data FROM lore_elements WHERE id = ? AND campaign_id = ?",
            (element_id, campaign_id)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        lore_type, element_data = result
        element_dict = json.loads(element_data)
        
        # Create the appropriate type of lore element
        if lore_type == LoreType.FACTION.value:
            return Faction.model_validate(element_dict)
        elif lore_type == LoreType.NPC.value:
            return NPC.model_validate(element_dict)
        elif lore_type == LoreType.PLACE.value:
            return Place.model_validate(element_dict)
        elif lore_type == LoreType.EVENT.value:
            return Event.model_validate(element_dict)
        elif lore_type == LoreType.FACT.value:
            return Fact.model_validate(element_dict)
        elif lore_type == LoreType.JOURNAL.value:
            return JournalEntry.model_validate(element_dict)
        else:
            return LoreElement.model_validate(element_dict)
    
    def delete_lore_element(self, campaign_id: str, element_id: str) -> bool:
        """
        Delete a lore element
        
        Args:
            campaign_id: ID of the campaign
            element_id: ID of the lore element
            
        Returns:
            True if element was deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM lore_elements WHERE id = ? AND campaign_id = ?",
            (element_id, campaign_id)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_lore_by_type(self, campaign_id: str, lore_type: LoreType, 
                         discovered_only: bool = False) -> List[LoreElement]:
        """
        Get all lore elements of a specific type
        
        Args:
            campaign_id: ID of the campaign
            lore_type: Type of lore elements to get
            discovered_only: Whether to only return discovered elements
            
        Returns:
            List of lore elements
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT element_data FROM lore_elements 
            WHERE campaign_id = ? AND lore_type = ?
        """
        params = [campaign_id, lore_type.value]
        
        if discovered_only:
            query += " AND discovered = 1"
        
        cursor.execute(query, params)
        
        elements = []
        for row in cursor.fetchall():
            element_dict = json.loads(row[0])
            
            # Create the appropriate type of lore element
            if lore_type == LoreType.FACTION:
                elements.append(Faction.model_validate(element_dict))
            elif lore_type == LoreType.NPC:
                elements.append(NPC.model_validate(element_dict))
            elif lore_type == LoreType.PLACE:
                elements.append(Place.model_validate(element_dict))
            elif lore_type == LoreType.EVENT:
                elements.append(Event.model_validate(element_dict))
            elif lore_type == LoreType.FACT:
                elements.append(Fact.model_validate(element_dict))
            elif lore_type == LoreType.JOURNAL:
                elements.append(JournalEntry.model_validate(element_dict))
            else:
                elements.append(LoreElement.model_validate(element_dict))
        
        conn.close()
        return elements
    
    def search_lore_by_tags(self, campaign_id: str, tags: List[str], 
                            match_all: bool = False, 
                            discovered_only: bool = False) -> List[LoreElement]:
        """
        Search for lore elements by tags
        
        Args:
            campaign_id: ID of the campaign
            tags: List of tags to search for
            match_all: Whether all tags must match (AND) or any tag (OR)
            discovered_only: Whether to only return discovered elements
            
        Returns:
            List of matching lore elements
        """
        if not tags:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build the query based on tag matching strategy
        query = "SELECT lore_type, element_data FROM lore_elements WHERE campaign_id = ?"
        params = [campaign_id]
        
        if discovered_only:
            query += " AND discovered = 1"
        
        # Add tag conditions
        if match_all:
            # All tags must match (AND)
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f"%{tag}%")
        else:
            # Any tag matches (OR)
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
            
            query += " AND (" + " OR ".join(tag_conditions) + ")"
        
        cursor.execute(query, params)
        
        elements = []
        for row in cursor.fetchall():
            lore_type, element_data = row
            element_dict = json.loads(element_data)
            
            # Create the appropriate type of lore element
            if lore_type == LoreType.FACTION.value:
                elements.append(Faction.model_validate(element_dict))
            elif lore_type == LoreType.NPC.value:
                elements.append(NPC.model_validate(element_dict))
            elif lore_type == LoreType.PLACE.value:
                elements.append(Place.model_validate(element_dict))
            elif lore_type == LoreType.EVENT.value:
                elements.append(Event.model_validate(element_dict))
            elif lore_type == LoreType.FACT.value:
                elements.append(Fact.model_validate(element_dict))
            elif lore_type == LoreType.JOURNAL.value:
                elements.append(JournalEntry.model_validate(element_dict))
            else:
                elements.append(LoreElement.model_validate(element_dict))
        
        conn.close()
        return elements
    
    def search_lore_by_text(self, campaign_id: str, search_text: str,
                           discovered_only: bool = False) -> List[LoreElement]:
        """
        Search for lore elements by text in name or description
        
        Args:
            campaign_id: ID of the campaign
            search_text: Text to search for
            discovered_only: Whether to only return discovered elements
            
        Returns:
            List of matching lore elements
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT lore_type, element_data FROM lore_elements 
            WHERE campaign_id = ? AND (name LIKE ? OR description LIKE ?)
        """
        params = [campaign_id, f"%{search_text}%", f"%{search_text}%"]
        
        if discovered_only:
            query += " AND discovered = 1"
        
        cursor.execute(query, params)
        
        elements = []
        for row in cursor.fetchall():
            lore_type, element_data = row
            element_dict = json.loads(element_data)
            
            # Create the appropriate type of lore element
            if lore_type == LoreType.FACTION.value:
                elements.append(Faction.model_validate(element_dict))
            elif lore_type == LoreType.NPC.value:
                elements.append(NPC.model_validate(element_dict))
            elif lore_type == LoreType.PLACE.value:
                elements.append(Place.model_validate(element_dict))
            elif lore_type == LoreType.EVENT.value:
                elements.append(Event.model_validate(element_dict))
            elif lore_type == LoreType.FACT.value:
                elements.append(Fact.model_validate(element_dict))
            elif lore_type == LoreType.JOURNAL.value:
                elements.append(JournalEntry.model_validate(element_dict))
            else:
                elements.append(LoreElement.model_validate(element_dict))
        
        conn.close()
        return elements
    
    def get_related_lore(self, campaign_id: str, element_id: str,
                        discovered_only: bool = False) -> List[LoreElement]:
        """
        Get all lore elements related to a specific element
        
        Args:
            campaign_id: ID of the campaign
            element_id: ID of the lore element
            discovered_only: Whether to only return discovered elements
            
        Returns:
            List of related lore elements
        """
        # First get the element to find its related elements
        element = self.get_lore_element(campaign_id, element_id)
        if not element:
            return []
        
        related_ids = element.related_elements
        if not related_ids:
            return []
        
        # Now get all the related elements
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ",".join(["?"] * len(related_ids))
        query = f"""
            SELECT lore_type, element_data FROM lore_elements 
            WHERE campaign_id = ? AND id IN ({placeholders})
        """
        params = [campaign_id] + related_ids
        
        if discovered_only:
            query += " AND discovered = 1"
        
        cursor.execute(query, params)
        
        elements = []
        for row in cursor.fetchall():
            lore_type, element_data = row
            element_dict = json.loads(element_data)
            
            # Create the appropriate type of lore element
            if lore_type == LoreType.FACTION.value:
                elements.append(Faction.model_validate(element_dict))
            elif lore_type == LoreType.NPC.value:
                elements.append(NPC.model_validate(element_dict))
            elif lore_type == LoreType.PLACE.value:
                elements.append(Place.model_validate(element_dict))
            elif lore_type == LoreType.EVENT.value:
                elements.append(Event.model_validate(element_dict))
            elif lore_type == LoreType.FACT.value:
                elements.append(Fact.model_validate(element_dict))
            elif lore_type == LoreType.JOURNAL.value:
                elements.append(JournalEntry.model_validate(element_dict))
            else:
                elements.append(LoreElement.model_validate(element_dict))
        
        conn.close()
        return elements
    
    def mark_as_discovered(self, campaign_id: str, element_id: str) -> bool:
        """
        Mark a lore element as discovered by the player
        
        Args:
            campaign_id: ID of the campaign
            element_id: ID of the lore element
            
        Returns:
            True if element was updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        discovery_time = datetime.now().isoformat()
        
        cursor.execute(
            """
            UPDATE lore_elements
            SET discovered = 1, discovery_timestamp = ?
            WHERE id = ? AND campaign_id = ? AND discovered = 0
            """,
            (discovery_time, element_id, campaign_id)
        )
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        # If updated, also update the element data JSON
        if updated:
            element = self.get_lore_element(campaign_id, element_id)
            if element:
                element.discovered = True
                element.discovery_timestamp = discovery_time
                self.add_lore_element(campaign_id, element)
        
        return updated
    
    def add_journal_entry(self, campaign_id: str, entry: JournalEntry) -> None:
        """
        Add a journal entry to the lore database
        
        Args:
            campaign_id: ID of the campaign
            entry: JournalEntry to add
        """
        # Ensure it's marked as a journal entry
        entry.lore_type = LoreType.JOURNAL
        
        # Set the timestamp if not already set
        if not entry.discovery_timestamp:
            entry.discovery_timestamp = datetime.now().isoformat()
        
        # Journal entries are always discovered
        entry.discovered = True
        
        # Add to the lore database
        self.add_lore_element(campaign_id, entry)
    
    def get_journal_entries(self, campaign_id: str, 
                           session_id: Optional[str] = None) -> List[JournalEntry]:
        """
        Get journal entries, optionally filtered by session
        
        Args:
            campaign_id: ID of the campaign
            session_id: Optional session ID to filter by
            
        Returns:
            List of journal entries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute(
                """
                SELECT element_data FROM lore_elements 
                WHERE campaign_id = ? AND lore_type = ? 
                AND element_data LIKE ?
                ORDER BY discovery_timestamp DESC
                """,
                (campaign_id, LoreType.JOURNAL.value, f'%"session_id":"{session_id}"%')
            )
        else:
            cursor.execute(
                """
                SELECT element_data FROM lore_elements 
                WHERE campaign_id = ? AND lore_type = ?
                ORDER BY discovery_timestamp DESC
                """,
                (campaign_id, LoreType.JOURNAL.value)
            )
        
        entries = []
        for row in cursor.fetchall():
            element_dict = json.loads(row[0])
            entries.append(JournalEntry.model_validate(element_dict))
        
        conn.close()
        return entries