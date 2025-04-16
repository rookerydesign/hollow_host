"""
Character Builder Module

Provides functionality for creating and customizing characters.
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from pydantic import ValidationError

from characters.character import Character, CharacterStats, CharacterSkills

class CharacterBuilder:
    """
    Builder for creating and customizing characters.
    """
    
    def __init__(self, data_dir: str = "characters/data"):
        """
        Initialize the character builder.
        
        Args:
            data_dir: Directory to store character data
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def create_character(self, character_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Character]]:
        """
        Create a new character from the provided data.
        
        Args:
            character_data: Dictionary containing character data
            
        Returns:
            Tuple of (success, message, character)
        """
        try:
            # Create stats object
            stats_data = character_data.get("stats", {})
            stats = CharacterStats(
                STR=stats_data.get("STR", 10),
                DEX=stats_data.get("DEX", 10),
                INT=stats_data.get("INT", 10),
                CHA=stats_data.get("CHA", 10),
                WIS=stats_data.get("WIS", 10),
                CON=stats_data.get("CON", 10)
            )
            
            # Create skills object
            skills_data = character_data.get("skills", {})
            skills = CharacterSkills(
                stealth=skills_data.get("stealth", 0),
                arcana=skills_data.get("arcana", 0),
                persuasion=skills_data.get("persuasion", 0)
            )
            
            # Create character object
            character = Character(
                name=character_data.get("name", ""),
                class_name=character_data.get("class", ""),
                level=character_data.get("level", 1),
                stats=stats,
                skills=skills,
                abilities=character_data.get("abilities", []),
                status_effects=character_data.get("status_effects", []),
                inventory=character_data.get("inventory", []),
                backstory=character_data.get("backstory", "")
            )
            
            # Save character to file
            filename = f"{character.name.lower().replace(' ', '_')}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            # Check if character already exists
            if os.path.exists(filepath):
                return False, f"Character with name '{character.name}' already exists.", None
            
            character.save_to_file(filepath)
            
            return True, f"Character '{character.name}' created successfully.", character
            
        except ValidationError as e:
            return False, f"Validation error: {str(e)}", None
        except Exception as e:
            return False, f"Error creating character: {str(e)}", None
    
    def update_character(self, name: str, character_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Character]]:
        """
        Update an existing character with the provided data.
        
        Args:
            name: Name of the character to update
            character_data: Dictionary containing updated character data
            
        Returns:
            Tuple of (success, message, character)
        """
        # Find character file
        filename = f"{name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return False, f"Character '{name}' not found.", None
        
        try:
            # Load existing character
            character = Character.load_from_file(filepath)
            
            # Update stats if provided
            if "stats" in character_data:
                stats_data = character_data["stats"]
                for stat, value in stats_data.items():
                    if hasattr(character.stats, stat):
                        setattr(character.stats, stat, value)
            
            # Update skills if provided
            if "skills" in character_data:
                skills_data = character_data["skills"]
                for skill, value in skills_data.items():
                    if hasattr(character.skills, skill):
                        setattr(character.skills, skill, value)
            
            # Update other fields if provided
            if "class" in character_data:
                character.class_name = character_data["class"]
            
            if "level" in character_data:
                character.level = character_data["level"]
            
            if "abilities" in character_data:
                character.abilities = character_data["abilities"]
            
            if "inventory" in character_data:
                character.inventory = character_data["inventory"]
            
            if "backstory" in character_data:
                character.backstory = character_data["backstory"]
            
            if "status_effects" in character_data:
                character.status_effects = character_data["status_effects"]
            
            # Save updated character
            character.save_to_file(filepath)
            
            return True, f"Character '{name}' updated successfully.", character
            
        except ValidationError as e:
            return False, f"Validation error: {str(e)}", None
        except Exception as e:
            return False, f"Error updating character: {str(e)}", None
    
    def delete_character(self, name: str) -> Tuple[bool, str]:
        """
        Delete a character.
        
        Args:
            name: Name of the character to delete
            
        Returns:
            Tuple of (success, message)
        """
        filename = f"{name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return False, f"Character '{name}' not found."
        
        try:
            os.remove(filepath)
            return True, f"Character '{name}' deleted successfully."
        except Exception as e:
            return False, f"Error deleting character: {str(e)}"
    
    def list_characters(self) -> List[Dict[str, Any]]:
        """
        List all available characters.
        
        Returns:
            List of character dictionaries with basic info
        """
        characters = []
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        characters.append({
                            "name": data.get("name", "Unknown"),
                            "class": data.get("class", "Unknown"),
                            "level": data.get("level", 1),
                            "filepath": filepath
                        })
                except Exception:
                    # Skip files that can't be parsed
                    continue
        
        return characters
    
    def get_character(self, name: str) -> Optional[Character]:
        """
        Get a character by name.
        
        Args:
            name: Name of the character to get
            
        Returns:
            Character object or None if not found
        """
        filename = f"{name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            return Character.load_from_file(filepath)
        except Exception:
            return None
    
    def save_character_image(self, character_name: str, image_data: bytes,
                           image_format: str = "png") -> Tuple[bool, str, Optional[str]]:
        """
        Save a character image.
        
        Args:
            character_name: Name of the character
            image_data: Binary image data
            image_format: Image format (png, jpg, etc.)
            
        Returns:
            Tuple of (success, message, image_path)
        """
        # Create images directory if it doesn't exist
        images_dir = os.path.join(self.data_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate a unique filename
        safe_name = character_name.lower().replace(' ', '_')
        filename = f"{safe_name}_{uuid.uuid4().hex[:8]}.{image_format}"
        filepath = os.path.join(images_dir, filename)
        
        try:
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Update character with image path
            character = self.get_character(character_name)
            if character:
                # Update the character with the image path
                character.image_path = filepath
                
                # Save the updated character
                character_path = os.path.join(self.data_dir, f"{safe_name}.json")
                character.save_to_file(character_path)
            
            return True, f"Image saved successfully for character '{character_name}'.", filepath
        except Exception as e:
            return False, f"Error saving image: {str(e)}", None
    
    def cli_character_creation_wizard(self) -> Tuple[bool, str, Optional[Character]]:
        """
        Run a CLI wizard for character creation.
        
        Returns:
            Tuple of (success, message, character)
        """
        print("=== Character Creation Wizard ===")
        
        # Get basic character info
        name = input("Character Name: ")
        class_name = input("Character Class: ")
        level = input("Level (default 1): ")
        level = int(level) if level.isdigit() else 1
        
        # Get stats
        print("\nEnter character stats (10 is average):")
        str_val = input("STR (default 10): ")
        dex_val = input("DEX (default 10): ")
        int_val = input("INT (default 10): ")
        cha_val = input("CHA (default 10): ")
        wis_val = input("WIS (default 10): ")
        con_val = input("CON (default 10): ")
        
        # Get skills
        print("\nEnter character skills (0 is untrained):")
        stealth = input("Stealth (default 0): ")
        arcana = input("Arcana (default 0): ")
        persuasion = input("Persuasion (default 0): ")
        
        # Get abilities
        print("\nEnter character abilities (comma-separated):")
        abilities_input = input("Abilities: ")
        abilities = [a.strip() for a in abilities_input.split(",") if a.strip()]
        
        # Get inventory
        print("\nEnter starting inventory (comma-separated):")
        inventory_input = input("Inventory: ")
        inventory = [i.strip() for i in inventory_input.split(",") if i.strip()]
        
        # Get backstory
        print("\nEnter character backstory:")
        backstory = input("Backstory: ")
        
        # Create character data dictionary
        character_data = {
            "name": name,
            "class": class_name,
            "level": level,
            "stats": {
                "STR": int(str_val) if str_val.isdigit() else 10,
                "DEX": int(dex_val) if dex_val.isdigit() else 10,
                "INT": int(int_val) if int_val.isdigit() else 10,
                "CHA": int(cha_val) if cha_val.isdigit() else 10,
                "WIS": int(wis_val) if wis_val.isdigit() else 10,
                "CON": int(con_val) if con_val.isdigit() else 10
            },
            "skills": {
                "stealth": int(stealth) if stealth.isdigit() else 0,
                "arcana": int(arcana) if arcana.isdigit() else 0,
                "persuasion": int(persuasion) if persuasion.isdigit() else 0
            },
            "abilities": abilities,
            "inventory": inventory,
            "backstory": backstory,
            "status_effects": []
        }
        
        # Create the character
        return self.create_character(character_data)