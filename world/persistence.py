"""
World Persistence Module

Handles saving, loading, and versioning of world state data.
"""

import json
import sqlite3
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from pydantic import BaseModel, Field
from characters.character import Character

class WorldLocation(BaseModel):
    """Model for storing location data"""
    name: str
    description: str
    connected_locations: List[str] = []
    discovered: bool = False
    tags: List[str] = []
    npcs_present: List[str] = []

class WorldState(BaseModel):
    """Model for storing complete world state"""
    campaign_id: str
    name: str
    version: int = 1
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    characters: Dict[str, Dict] = {}  # Store as dict for serialization
    locations: Dict[str, WorldLocation] = {}
    active_quests: List[str] = []
    completed_quests: List[str] = []
    world_flags: Dict[str, Any] = {}  # For storing arbitrary state flags
    
    def add_character(self, character: Character) -> None:
        """Add or update a character in the world state"""
        self.characters[character.name] = character.model_dump()
    
    def add_location(self, location: WorldLocation) -> None:
        """Add or update a location in the world state"""
        self.locations[location.name] = location
    
    def set_flag(self, key: str, value: Any) -> None:
        """Set a world state flag"""
        self.world_flags[key] = value
    
    def get_flag(self, key: str, default: Any = None) -> Any:
        """Get a world state flag"""
        return self.world_flags.get(key, default)

class SaveManager:
    """Handles saving and loading of world state with versioning"""
    
    def __init__(self, base_path: str = "./saves"):
        """Initialize the save manager with a base path for saves"""
        self.base_path = base_path
        self.db_path = os.path.join(base_path, "world_state.db")
        os.makedirs(base_path, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database for storing world states"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for world state and version tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS world_states (
                campaign_id TEXT,
                version INTEGER,
                timestamp TEXT,
                state_data TEXT,
                PRIMARY KEY (campaign_id, version)
            )
        """)
        
        # Create table for autosave triggers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autosave_events (
                campaign_id TEXT,
                event_type TEXT,
                timestamp TEXT,
                version INTEGER,
                FOREIGN KEY (campaign_id, version) 
                REFERENCES world_states (campaign_id, version)
            )
        """)
        
        conn.commit()
        conn.close()

    def save_world_state(self, state: WorldState, auto_save: bool = False, 
                         event_type: Optional[str] = None) -> None:
        """
        Save the current world state with versioning
        
        Args:
            state: WorldState object to save
            auto_save: Whether this is an automatic save
            event_type: Type of event that triggered the autosave
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Increment version for the campaign
        cursor.execute(
            "SELECT MAX(version) FROM world_states WHERE campaign_id = ?",
            (state.campaign_id,)
        )
        result = cursor.fetchone()
        current_version = result[0] if result[0] is not None else 0
        state.version = current_version + 1
        
        # Update timestamp
        state.timestamp = datetime.now().isoformat()
        
        # Save the state
        state_json = state.model_dump_json()
        cursor.execute(
            "INSERT INTO world_states (campaign_id, version, timestamp, state_data) VALUES (?, ?, ?, ?)",
            (state.campaign_id, state.version, state.timestamp, state_json)
        )
        
        # Record autosave event if applicable
        if auto_save and event_type:
            cursor.execute(
                "INSERT INTO autosave_events (campaign_id, event_type, timestamp, version) VALUES (?, ?, ?, ?)",
                (state.campaign_id, event_type, state.timestamp, state.version)
            )
        
        conn.commit()
        conn.close()
        
        # Also save a JSON backup
        json_path = os.path.join(
            self.base_path, 
            f"{state.campaign_id}_v{state.version}.json"
        )
        with open(json_path, 'w') as f:
            f.write(state_json)

    def load_world_state(self, campaign_id: str, version: Optional[int] = None) -> WorldState:
        """
        Load a world state by campaign ID and optionally version
        
        Args:
            campaign_id: ID of the campaign to load
            version: Specific version to load, or None for latest
            
        Returns:
            The loaded WorldState
            
        Raises:
            ValueError: If the campaign or version doesn't exist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if version is None:
            # Get the latest version
            cursor.execute(
                "SELECT MAX(version) FROM world_states WHERE campaign_id = ?",
                (campaign_id,)
            )
            result = cursor.fetchone()
            if result[0] is None:
                conn.close()
                raise ValueError(f"No saved states found for campaign {campaign_id}")
            version = result[0]
        
        # Load the state data
        cursor.execute(
            "SELECT state_data FROM world_states WHERE campaign_id = ? AND version = ?",
            (campaign_id, version)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            raise ValueError(f"No saved state found for campaign {campaign_id} version {version}")
        
        state_data = json.loads(result[0])
        return WorldState.model_validate(state_data)

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        List all available campaigns with their latest versions
        
        Returns:
            List of campaign info dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ws.campaign_id, ws.version, ws.timestamp, json_extract(ws.state_data, '$.name')
            FROM world_states ws
            INNER JOIN (
                SELECT campaign_id, MAX(version) as max_version
                FROM world_states
                GROUP BY campaign_id
            ) latest
            ON ws.campaign_id = latest.campaign_id AND ws.version = latest.max_version
        """)
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                'campaign_id': row[0],
                'latest_version': row[1],
                'last_updated': row[2],
                'name': row[3]
            })
        
        conn.close()
        return campaigns

    def list_versions(self, campaign_id: str) -> List[Dict[str, Any]]:
        """
        List all versions for a specific campaign
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            List of version info dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version, timestamp, 
                   (SELECT event_type FROM autosave_events 
                    WHERE campaign_id = ? AND version = world_states.version)
            FROM world_states
            WHERE campaign_id = ?
            ORDER BY version DESC
        """, (campaign_id, campaign_id))
        
        versions = []
        for row in cursor.fetchall():
            versions.append({
                'version': row[0],
                'timestamp': row[1],
                'event_type': row[2],
                'is_autosave': row[2] is not None
            })
        
        conn.close()
        return versions

    def export_campaign(self, campaign_id: str, export_path: str) -> str:
        """
        Export a campaign to a ZIP file with all versions
        
        Args:
            campaign_id: ID of the campaign to export
            export_path: Directory to export to
            
        Returns:
            Path to the created ZIP file
        """
        # Create a temporary directory for export
        temp_dir = os.path.join(self.base_path, f"temp_export_{campaign_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Export all versions as JSON
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT version, state_data FROM world_states WHERE campaign_id = ? ORDER BY version",
            (campaign_id,)
        )
        
        for row in cursor.fetchall():
            version, state_data = row
            with open(os.path.join(temp_dir, f"version_{version}.json"), 'w') as f:
                f.write(state_data)
        
        # Export autosave events
        cursor.execute(
            "SELECT version, event_type, timestamp FROM autosave_events WHERE campaign_id = ? ORDER BY version",
            (campaign_id,)
        )
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'version': row[0],
                'event_type': row[1],
                'timestamp': row[2]
            })
        
        with open(os.path.join(temp_dir, "autosave_events.json"), 'w') as f:
            json.dump(events, f, indent=2)
        
        conn.close()
        
        # Create ZIP file
        zip_path = os.path.join(export_path, f"{campaign_id}_export.zip")
        shutil.make_archive(
            os.path.splitext(zip_path)[0],  # Remove .zip extension for make_archive
            'zip',
            temp_dir
        )
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        return zip_path

    def import_campaign(self, zip_path: str) -> str:
        """
        Import a campaign from a ZIP file
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            The imported campaign ID
        """
        # Extract ZIP to temporary directory
        temp_dir = os.path.join(self.base_path, "temp_import")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        shutil.unpack_archive(zip_path, temp_dir, 'zip')
        
        # Get campaign ID from first version file
        version_files = [f for f in os.listdir(temp_dir) if f.startswith("version_")]
        if not version_files:
            raise ValueError("Invalid export file: no version data found")
        
        with open(os.path.join(temp_dir, version_files[0]), 'r') as f:
            first_version = json.load(f)
            campaign_id = first_version.get('campaign_id')
            
        if not campaign_id:
            raise ValueError("Invalid export file: missing campaign ID")
        
        # Import all versions
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data for this campaign if it exists
        cursor.execute("DELETE FROM autosave_events WHERE campaign_id = ?", (campaign_id,))
        cursor.execute("DELETE FROM world_states WHERE campaign_id = ?", (campaign_id,))
        
        # Import versions
        for filename in version_files:
            with open(os.path.join(temp_dir, filename), 'r') as f:
                state_data = f.read()
                state = json.loads(state_data)
                cursor.execute(
                    "INSERT INTO world_states (campaign_id, version, timestamp, state_data) VALUES (?, ?, ?, ?)",
                    (campaign_id, state['version'], state['timestamp'], state_data)
                )
        
        # Import autosave events if present
        events_path = os.path.join(temp_dir, "autosave_events.json")
        if os.path.exists(events_path):
            with open(events_path, 'r') as f:
                events = json.load(f)
                for event in events:
                    cursor.execute(
                        "INSERT INTO autosave_events (campaign_id, event_type, timestamp, version) VALUES (?, ?, ?, ?)",
                        (campaign_id, event['event_type'], event['timestamp'], event['version'])
                    )
        
        conn.commit()
        conn.close()
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return campaign_id

    def get_diff(self, campaign_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        Get a diff between two versions of a campaign
        
        Args:
            campaign_id: ID of the campaign
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Dictionary with changes between versions
        """
        state1 = self.load_world_state(campaign_id, version1)
        state2 = self.load_world_state(campaign_id, version2)
        
        diff = {
            'characters': self._diff_characters(state1, state2),
            'locations': self._diff_locations(state1, state2),
            'quests': self._diff_quests(state1, state2),
            'flags': self._diff_flags(state1, state2)
        }
        
        return diff
    
    def _diff_characters(self, state1: WorldState, state2: WorldState) -> Dict[str, Any]:
        """Compare characters between two states"""
        chars1 = set(state1.characters.keys())
        chars2 = set(state2.characters.keys())
        
        added = chars2 - chars1
        removed = chars1 - chars2
        modified = set()
        
        for char_name in chars1.intersection(chars2):
            if state1.characters[char_name] != state2.characters[char_name]:
                modified.add(char_name)
        
        return {
            'added': list(added),
            'removed': list(removed),
            'modified': list(modified)
        }
    
    def _diff_locations(self, state1: WorldState, state2: WorldState) -> Dict[str, Any]:
        """Compare locations between two states"""
        locs1 = set(state1.locations.keys())
        locs2 = set(state2.locations.keys())
        
        added = locs2 - locs1
        removed = locs1 - locs2
        modified = set()
        
        for loc_name in locs1.intersection(locs2):
            if state1.locations[loc_name].model_dump() != state2.locations[loc_name].model_dump():
                modified.add(loc_name)
        
        return {
            'added': list(added),
            'removed': list(removed),
            'modified': list(modified)
        }
    
    def _diff_quests(self, state1: WorldState, state2: WorldState) -> Dict[str, Any]:
        """Compare quests between two states"""
        active1 = set(state1.active_quests)
        active2 = set(state2.active_quests)
        completed1 = set(state1.completed_quests)
        completed2 = set(state2.completed_quests)
        
        return {
            'new_active': list(active2 - active1),
            'completed': list(completed2 - completed1),
            'abandoned': list(active1 - active2 - completed2)
        }
    
    def _diff_flags(self, state1: WorldState, state2: WorldState) -> Dict[str, Any]:
        """Compare world flags between two states"""
        flags1 = set(state1.world_flags.keys())
        flags2 = set(state2.world_flags.keys())
        
        added = flags2 - flags1
        removed = flags1 - flags2
        modified = set()
        
        for flag in flags1.intersection(flags2):
            if state1.world_flags[flag] != state2.world_flags[flag]:
                modified.add(flag)
        
        return {
            'added': {k: state2.world_flags[k] for k in added},
            'removed': list(removed),
            'modified': {k: (state1.world_flags[k], state2.world_flags[k]) for k in modified}
        }