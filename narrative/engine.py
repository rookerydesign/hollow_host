"""
Narrative Engine Module

Handles narrative generation, scene management, and story progression.
"""

from typing import Dict, List, Any, Optional
import re

class NarrativeEngine:
    """
    Engine for managing narrative generation and story progression.
    """
    
    def __init__(self):
        """Initialize the narrative engine."""
        self.current_scene = "You stand at the entrance of a dark, mysterious cave."
        self.current_location = "Cave Entrance"
        self.story_beats = []
        self.key_npcs = {}
        self.discovered_locations = ["Cave Entrance"]
        self.active_quests = []
    
    def update_scene(self, new_scene: str) -> None:
        """
        Update the current scene description.
        
        Args:
            new_scene: The new scene description
        """
        self.current_scene = new_scene
    
    def update_location(self, location: str) -> None:
        """
        Update the current location.
        
        Args:
            location: The new location name
        """
        self.current_location = location
        
        # Add to discovered locations if not already there
        if location not in self.discovered_locations:
            self.discovered_locations.append(location)
    
    def add_story_beat(self, beat: str) -> None:
        """
        Add a story beat to the narrative.
        
        Args:
            beat: The story beat to add
        """
        self.story_beats.append(beat)
    
    def add_npc(self, name: str, description: str, role: str = "minor") -> None:
        """
        Add an NPC to the narrative.
        
        Args:
            name: The NPC's name
            description: Description of the NPC
            role: The NPC's role in the story (major, minor, etc.)
        """
        self.key_npcs[name] = {
            "description": description,
            "role": role,
            "first_seen": self.current_location,
            "disposition": "neutral"
        }
    
    def update_npc(self, name: str, updates: Dict[str, Any]) -> None:
        """
        Update an NPC's information.
        
        Args:
            name: The NPC's name
            updates: Dictionary of attributes to update
        """
        if name in self.key_npcs:
            self.key_npcs[name].update(updates)
    
    def add_quest(self, title: str, description: str, objectives: List[str]) -> None:
        """
        Add a new quest to the narrative.
        
        Args:
            title: The quest title
            description: Description of the quest
            objectives: List of quest objectives
        """
        quest = {
            "title": title,
            "description": description,
            "objectives": objectives,
            "status": "active",
            "progress": {obj: "incomplete" for obj in objectives},
            "location_given": self.current_location
        }
        
        self.active_quests.append(quest)
    
    def update_quest_progress(self, quest_title: str, objective: str, status: str = "complete") -> None:
        """
        Update the progress of a quest objective.
        
        Args:
            quest_title: The title of the quest
            objective: The objective to update
            status: The new status of the objective
        """
        for quest in self.active_quests:
            if quest["title"] == quest_title:
                if objective in quest["progress"]:
                    quest["progress"][objective] = status
                
                # Check if all objectives are complete
                all_complete = all(status == "complete" for status in quest["progress"].values())
                if all_complete:
                    quest["status"] = "completed"
    
    def extract_narrative_elements(self, text: str) -> Dict[str, Any]:
        """
        Extract narrative elements from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary of extracted narrative elements
        """
        elements = {
            "locations": [],
            "npcs": [],
            "items": [],
            "events": []
        }
        
        # Extract locations (simple implementation - would be more sophisticated in practice)
        location_pattern = r'(?:at|in|to) the ([A-Z][a-z]+(?: [A-Z][a-z]+)*)'
        locations = re.findall(location_pattern, text)
        elements["locations"] = list(set(locations))
        
        # Extract NPCs (names are capitalized words not at the start of sentences)
        npc_pattern = r'(?<!^)(?<![\.\?!]\s)([A-Z][a-z]+)'
        npcs = re.findall(npc_pattern, text)
        elements["npcs"] = list(set(npcs))
        
        # Extract items (things in quotes or after "find", "take", "use", etc.)
        item_pattern = r'"([^"]+)"|(?:find|take|use|carry|wield) (?:the|a|an) ([a-z]+(?:\s[a-z]+)*)'
        items = re.findall(item_pattern, text)
        # Flatten and clean the items list
        flat_items = []
        for item_tuple in items:
            flat_items.extend([i for i in item_tuple if i])
        elements["items"] = list(set(flat_items))
        
        return elements
    
    def generate_scene_description(self, location: str, time_of_day: str = "day", 
                                  mood: str = "neutral") -> str:
        """
        Generate a scene description based on location and parameters.
        
        Args:
            location: The location name
            time_of_day: Time of day (day, night, dawn, dusk)
            mood: The mood of the scene (neutral, tense, peaceful, etc.)
            
        Returns:
            A scene description (placeholder implementation)
        """
        # This is a placeholder - in the real implementation, this would use the LLM
        # to generate a dynamic scene description
        
        descriptions = {
            "Cave Entrance": {
                "day": "Sunlight filters through the trees, illuminating the mouth of the cave.",
                "night": "The cave mouth is a dark void against the moonlit forest.",
                "dawn": "The first rays of sunlight touch the cave entrance, revealing moss-covered stones.",
                "dusk": "Long shadows stretch from the trees as the sun sets behind the cave entrance."
            },
            "Forest Path": {
                "day": "Dappled sunlight filters through the dense canopy of leaves above the forest path.",
                "night": "The forest path is barely visible in the darkness, with only occasional moonlight breaking through.",
                "dawn": "Morning mist clings to the forest floor as light gradually fills the path.",
                "dusk": "The forest path darkens as the sun sets, with the last golden rays streaming between tree trunks."
            },
            "Village Square": {
                "day": "The village square bustles with activity under the bright sun.",
                "night": "Lanterns cast a warm glow across the empty village square.",
                "dawn": "The village square is quiet as the first villagers begin to stir with the rising sun.",
                "dusk": "The village square grows quiet as people head home for the evening."
            }
        }
        
        # Default description if location not found
        if location not in descriptions:
            return f"You are at {location}. The area is quiet and still."
        
        # Get description based on time of day
        if time_of_day not in descriptions[location]:
            time_of_day = "day"  # Default to day if time not found
            
        base_description = descriptions[location][time_of_day]
        
        # Add mood modifiers
        mood_modifiers = {
            "tense": "There's a palpable tension in the air, making you uneasy.",
            "peaceful": "A sense of peace and tranquility surrounds you.",
            "mysterious": "Something about this place feels mysterious and unknown.",
            "dangerous": "You sense danger lurking nearby, putting you on edge."
        }
        
        if mood in mood_modifiers:
            return f"{base_description} {mood_modifiers[mood]}"
        
        return base_description
    
    def get_narrative_context(self, include_history: bool = True) -> Dict[str, Any]:
        """
        Get the current narrative context.
        
        Args:
            include_history: Whether to include story history
            
        Returns:
            Dictionary of narrative context
        """
        context = {
            "current_scene": self.current_scene,
            "current_location": self.current_location,
            "discovered_locations": self.discovered_locations,
            "key_npcs": self.key_npcs,
            "active_quests": self.active_quests
        }
        
        if include_history:
            context["story_beats"] = self.story_beats
        
        return context

# TODO: Add support for branching narratives
# TODO: Add support for dynamic NPC behavior based on player actions
# TODO: Add support for environmental storytelling