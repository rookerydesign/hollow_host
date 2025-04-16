"""
Character Module

Handles character data, loading/saving, applying modifiers, and tracking progression.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator
import os
import uuid

class CharacterStats(BaseModel):
    """Character statistics model"""
    STR: int
    DEX: int
    INT: int
    CHA: int
    WIS: int
    CON: int
    
    def get_modifier(self, stat: str) -> int:
        """
        Calculate the modifier for a given stat.
        
        Args:
            stat: The stat to calculate modifier for (STR, DEX, etc.)
            
        Returns:
            The calculated modifier value
        """
        stat_value = getattr(self, stat)
        # Standard D&D-style modifier calculation: (stat - 10) // 2
        return (stat_value - 10) // 2

class CharacterSkills(BaseModel):
    """Character skills model"""
    stealth: int = 0
    arcana: int = 0
    persuasion: int = 0
    # Add more skills as needed

class CharacterChange(BaseModel):
    """Model for tracking character changes over time"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    change_type: str  # level_up, stat_change, ability_added, etc.
    description: str
    previous_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Dict[str, Any] = {}

class Character(BaseModel):
    """
    Character model for storing and managing character data.
    """
    name: str
    class_name: str = Field(..., alias="class")
    level: int
    stats: CharacterStats
    skills: CharacterSkills = CharacterSkills()
    abilities: List[str] = []
    status_effects: List[str] = []
    inventory: List[str] = []
    backstory: Optional[str] = None
    image_path: Optional[str] = None
    xp: int = 0
    max_hp: int = 10
    current_hp: int = 10
    changelog: List[CharacterChange] = []
    
    class Config:
        """Pydantic configuration"""
        populate_by_name = True
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Character':
        """
        Load a character from a JSON file.
        
        Args:
            filepath: Path to the character JSON file
            
        Returns:
            Character object
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Character file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls(**data)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the character to a JSON file.
        
        Args:
            filepath: Path to save the character JSON file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(self.model_dump_json(indent=2))
    
    def apply_status_effect(self, effect: str, session_id: Optional[str] = None) -> None:
        """
        Apply a status effect to the character and record the change.
        
        Args:
            effect: The status effect to apply
            session_id: Optional ID of the current session
        """
        if effect not in self.status_effects:
            self.status_effects.append(effect)
            
            # Record the change
            self.changelog.append(CharacterChange(
                session_id=session_id,
                change_type="status_effect_applied",
                description=f"Applied status effect: {effect}",
                new_value=effect
            ))
    
    def remove_status_effect(self, effect: str, session_id: Optional[str] = None) -> None:
        """
        Remove a status effect from the character and record the change.
        
        Args:
            effect: The status effect to remove
            session_id: Optional ID of the current session
        """
        if effect in self.status_effects:
            self.status_effects.remove(effect)
            
            # Record the change
            self.changelog.append(CharacterChange(
                session_id=session_id,
                change_type="status_effect_removed",
                description=f"Removed status effect: {effect}",
                previous_value=effect
            ))
    
    def add_to_inventory(self, item: str, session_id: Optional[str] = None) -> None:
        """
        Add an item to the character's inventory and record the change.
        
        Args:
            item: The item to add
            session_id: Optional ID of the current session
        """
        self.inventory.append(item)
        
        # Record the change
        self.changelog.append(CharacterChange(
            session_id=session_id,
            change_type="item_acquired",
            description=f"Added item to inventory: {item}",
            new_value=item
        ))
    
    def remove_from_inventory(self, item: str, session_id: Optional[str] = None) -> None:
        """
        Remove an item from the character's inventory and record the change.
        
        Args:
            item: The item to remove
            session_id: Optional ID of the current session
        """
        if item in self.inventory:
            self.inventory.remove(item)
            
            # Record the change
            self.changelog.append(CharacterChange(
                session_id=session_id,
                change_type="item_removed",
                description=f"Removed item from inventory: {item}",
                previous_value=item
            ))
    
    def level_up(self, session_id: Optional[str] = None) -> None:
        """
        Increase the character's level by 1 and record the change.
        
        Args:
            session_id: Optional ID of the current session
        """
        previous_level = self.level
        self.level += 1
        
        # Record the change
        self.changelog.append(CharacterChange(
            session_id=session_id,
            change_type="level_up",
            description=f"Advanced from level {previous_level} to {self.level}",
            previous_value=previous_level,
            new_value=self.level
        ))
    
    def add_ability(self, ability: str, session_id: Optional[str] = None) -> None:
        """
        Add a new ability to the character and record the change.
        
        Args:
            ability: The ability to add
            session_id: Optional ID of the current session
        """
        if ability not in self.abilities:
            self.abilities.append(ability)
            
            # Record the change
            self.changelog.append(CharacterChange(
                session_id=session_id,
                change_type="ability_added",
                description=f"Gained new ability: {ability}",
                new_value=ability
            ))
    
    def apply_stat_change(self, stat: str, value: int,
                         session_id: Optional[str] = None) -> None:
        """
        Apply a change to a character stat and record the change.
        
        Args:
            stat: The stat to modify (STR, DEX, etc.)
            value: The amount to change the stat by (can be negative)
            session_id: Optional ID of the current session
        """
        if hasattr(self.stats, stat):
            previous_value = getattr(self.stats, stat)
            new_value = previous_value + value
            setattr(self.stats, stat, new_value)
            
            # Record the change
            self.changelog.append(CharacterChange(
                session_id=session_id,
                change_type="stat_change",
                description=f"{stat} changed from {previous_value} to {new_value}",
                previous_value=previous_value,
                new_value=new_value,
                metadata={"stat": stat, "change_amount": value}
            ))
    
    def apply_skill_change(self, skill: str, value: int,
                          session_id: Optional[str] = None) -> None:
        """
        Apply a change to a character skill and record the change.
        
        Args:
            skill: The skill to modify
            value: The amount to change the skill by (can be negative)
            session_id: Optional ID of the current session
        """
        if hasattr(self.skills, skill):
            previous_value = getattr(self.skills, skill)
            new_value = previous_value + value
            setattr(self.skills, skill, new_value)
            
            # Record the change
            self.changelog.append(CharacterChange(
                session_id=session_id,
                change_type="skill_change",
                description=f"{skill} changed from {previous_value} to {new_value}",
                previous_value=previous_value,
                new_value=new_value,
                metadata={"skill": skill, "change_amount": value}
            ))
    
    def get_skill_modifier(self, skill: str) -> int:
        """
        Get the total modifier for a skill including stat bonus.
        
        Args:
            skill: The skill name
            
        Returns:
            The total skill modifier
        """
        # Map skills to their primary stats
        skill_stat_map = {
            "stealth": "DEX",
            "arcana": "INT",
            "persuasion": "CHA",
            # Add more mappings as needed
        }
        
        # Get the base skill value
        skill_value = getattr(self.skills, skill, 0)
        
        # Add the stat modifier if the skill has a stat mapping
        if skill in skill_stat_map:
            stat = skill_stat_map[skill]
            skill_value += self.stats.get_modifier(stat)
        
        return skill_value
    
    def get_image_url(self) -> Optional[str]:
        """
        Get the URL for the character's image.
        
        Returns:
            The image URL or None if no image is set
        """
        if not self.image_path:
            return None
        
        # Convert backslashes to forward slashes for URLs
        path = self.image_path.replace("\\", "/")
        
        # If the path is absolute, convert to relative URL
        if os.path.isabs(path):
            # Extract the relative path from the characters/data/images directory
            parts = path.split("characters/data/images/")
            if len(parts) > 1:
                return f"/static/character_images/{parts[1]}"
            return None
        
        # If already a relative path, ensure it starts with /static/
        if not path.startswith("/static/"):
            return f"/static/character_images/{os.path.basename(path)}"
        
        return path
    
    def add_xp(self, amount: int, session_id: Optional[str] = None) -> bool:
        """
        Add experience points to the character and level up if threshold reached.
        
        Args:
            amount: Amount of XP to add
            session_id: Optional ID of the current session
            
        Returns:
            True if the character leveled up, False otherwise
        """
        previous_xp = self.xp
        self.xp += amount
        
        # Record the XP change
        self.changelog.append(CharacterChange(
            session_id=session_id,
            change_type="xp_gained",
            description=f"Gained {amount} XP ({previous_xp} → {self.xp})",
            previous_value=previous_xp,
            new_value=self.xp,
            metadata={"amount": amount}
        ))
        
        # Check if level up is triggered
        # Simple XP threshold: level * 100
        if self.xp >= self.level * 100:
            self.level_up(session_id)
            return True
        
        return False
    
    def heal(self, amount: int, session_id: Optional[str] = None) -> None:
        """
        Heal the character by the specified amount.
        
        Args:
            amount: Amount of HP to heal
            session_id: Optional ID of the current session
        """
        previous_hp = self.current_hp
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        
        # Record the healing
        self.changelog.append(CharacterChange(
            session_id=session_id,
            change_type="healed",
            description=f"Healed for {amount} HP ({previous_hp} → {self.current_hp})",
            previous_value=previous_hp,
            new_value=self.current_hp,
            metadata={"amount": amount}
        ))
    
    def take_damage(self, amount: int, session_id: Optional[str] = None) -> bool:
        """
        Apply damage to the character.
        
        Args:
            amount: Amount of damage to apply
            session_id: Optional ID of the current session
            
        Returns:
            True if the character is reduced to 0 HP, False otherwise
        """
        previous_hp = self.current_hp
        self.current_hp = max(self.current_hp - amount, 0)
        
        # Record the damage
        self.changelog.append(CharacterChange(
            session_id=session_id,
            change_type="damaged",
            description=f"Took {amount} damage ({previous_hp} → {self.current_hp})",
            previous_value=previous_hp,
            new_value=self.current_hp,
            metadata={"amount": amount}
        ))
        
        return self.current_hp == 0
    
    def get_changes_by_session(self, session_id: str) -> List[CharacterChange]:
        """
        Get all changes that occurred during a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of CharacterChange objects for the session
        """
        return [change for change in self.changelog if change.session_id == session_id]
    
    def get_changes_by_type(self, change_type: str) -> List[CharacterChange]:
        """
        Get all changes of a specific type.
        
        Args:
            change_type: Type of changes to get
            
        Returns:
            List of CharacterChange objects of the specified type
        """
        return [change for change in self.changelog if change.change_type == change_type]
    
    def revert_to_version(self, timestamp: str) -> None:
        """
        Revert character to a previous state based on changelog.
        
        Args:
            timestamp: Timestamp to revert to (will revert to state just after this timestamp)
        """
        # Filter changes that occurred after the specified timestamp
        changes_to_revert = [c for c in self.changelog if c.timestamp > timestamp]
        changes_to_revert.reverse()  # Process in reverse chronological order
        
        for change in changes_to_revert:
            if change.change_type == "level_up" and change.previous_value is not None:
                self.level = change.previous_value
            elif change.change_type == "ability_added" and change.new_value is not None:
                if change.new_value in self.abilities:
                    self.abilities.remove(change.new_value)
            elif change.change_type == "stat_change" and change.metadata.get("stat") and change.previous_value is not None:
                setattr(self.stats, change.metadata["stat"], change.previous_value)
            elif change.change_type == "skill_change" and change.metadata.get("skill") and change.previous_value is not None:
                setattr(self.skills, change.metadata["skill"], change.previous_value)
            elif change.change_type == "status_effect_applied" and change.new_value is not None:
                if change.new_value in self.status_effects:
                    self.status_effects.remove(change.new_value)
            elif change.change_type == "status_effect_removed" and change.previous_value is not None:
                if change.previous_value not in self.status_effects:
                    self.status_effects.append(change.previous_value)
            elif change.change_type == "item_acquired" and change.new_value is not None:
                if change.new_value in self.inventory:
                    self.inventory.remove(change.new_value)
            elif change.change_type == "item_removed" and change.previous_value is not None:
                if change.previous_value not in self.inventory:
                    self.inventory.append(change.previous_value)
            elif change.change_type == "xp_gained" and change.previous_value is not None:
                self.xp = change.previous_value
            elif change.change_type in ["healed", "damaged"] and change.previous_value is not None:
                self.current_hp = change.previous_value
        
        # Remove the reverted changes from the changelog
        self.changelog = [c for c in self.changelog if c.timestamp <= timestamp]

# Equipment and progression systems are now implemented