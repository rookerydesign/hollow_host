"""
Character Module

Handles character data, loading/saving, and applying modifiers.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
import os

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
    
    def apply_status_effect(self, effect: str) -> None:
        """
        Apply a status effect to the character.
        
        Args:
            effect: The status effect to apply
        """
        if effect not in self.status_effects:
            self.status_effects.append(effect)
    
    def remove_status_effect(self, effect: str) -> None:
        """
        Remove a status effect from the character.
        
        Args:
            effect: The status effect to remove
        """
        if effect in self.status_effects:
            self.status_effects.remove(effect)
    
    def add_to_inventory(self, item: str) -> None:
        """
        Add an item to the character's inventory.
        
        Args:
            item: The item to add
        """
        self.inventory.append(item)
    
    def remove_from_inventory(self, item: str) -> None:
        """
        Remove an item from the character's inventory.
        
        Args:
            item: The item to remove
        """
        if item in self.inventory:
            self.inventory.remove(item)
    
    def level_up(self) -> None:
        """Increase the character's level by 1."""
        self.level += 1
    
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

# TODO: Add support for equipment that modifies stats
# TODO: Add support for class-specific abilities
# TODO: Add support for character progression and experience points