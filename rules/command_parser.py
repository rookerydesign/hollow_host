"""
Command Parser Module

Interprets player input to determine if it's a command, roll, or narrative text.
"""

import re
import random
from typing import Dict, Tuple, Any, Optional, List

class CommandParser:
    """
    Parser for interpreting player commands, dice rolls, and actions.
    """
    
    # Command patterns
    ROLL_PATTERN = r'/roll\s+(\d+)d(\d+)(?:\s*\+\s*(\w+))?'
    ACTION_PATTERN = r'/(\w+)(?:\s+(.+))?'
    
    def __init__(self):
        """Initialize the command parser."""
        # Register available commands
        self.commands = {
            'help': self._help_command,
            'inventory': self._inventory_command,
            'stats': self._stats_command,
            'look': self._look_command,
            'use': self._use_command,
            # Add more commands as needed
        }
    
    def parse(self, text: str, character: Any = None) -> Tuple[str, Dict[str, Any]]:
        """
        Parse the player's input text to determine if it's a command, roll, or narrative.
        
        Args:
            text: The player's input text
            character: Optional character object for context-aware commands
            
        Returns:
            Tuple of (command_type, result_dict)
        """
        # Check if it's a dice roll
        roll_match = re.match(self.ROLL_PATTERN, text)
        if roll_match:
            return self._handle_roll(roll_match, character)
        
        # Check if it's a command
        action_match = re.match(self.ACTION_PATTERN, text)
        if action_match:
            return self._handle_command(action_match, character)
        
        # If not a command or roll, treat as narrative input
        return 'narrative', {'text': text}
    
    def _handle_roll(self, match: re.Match, character: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Handle a dice roll command.
        
        Args:
            match: The regex match object
            character: Character object for stat modifiers
            
        Returns:
            Tuple of ('roll', result_dict)
        """
        num_dice = int(match.group(1))
        dice_type = int(match.group(2))
        modifier_name = match.group(3)
        
        # Roll the dice
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        base_total = sum(rolls)
        
        # Apply modifier if specified and character is provided
        modifier_value = 0
        if modifier_name and character:
            # Check if it's a stat
            if hasattr(character.stats, modifier_name):
                modifier_value = character.stats.get_modifier(modifier_name)
            # Check if it's a skill
            elif hasattr(character.skills, modifier_name):
                modifier_value = character.get_skill_modifier(modifier_name)
        
        total = base_total + modifier_value
        
        return 'roll', {
            'rolls': rolls,
            'dice_type': dice_type,
            'modifier_name': modifier_name,
            'modifier_value': modifier_value,
            'total': total
        }
    
    def _handle_command(self, match: re.Match, character: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Handle a command.
        
        Args:
            match: The regex match object
            character: Character object for context
            
        Returns:
            Tuple of ('command', result_dict)
        """
        command = match.group(1).lower()
        args = match.group(2) if match.group(2) else ""
        
        if command in self.commands:
            return 'command', self.commands[command](args, character)
        else:
            return 'command', {
                'success': False,
                'message': f"Unknown command: {command}. Type /help for available commands."
            }
    
    def _help_command(self, args: str, character: Any) -> Dict[str, Any]:
        """Display help information."""
        available_commands = [
            "/roll XdY+STAT - Roll X dice with Y sides plus STAT modifier",
            "/help - Show this help message",
            "/inventory - Show your inventory",
            "/stats - Show your character stats",
            "/look - Look around the current area",
            "/use ITEM - Use an item from your inventory"
        ]
        
        return {
            'success': True,
            'message': "Available commands:\n" + "\n".join(available_commands)
        }
    
    def _inventory_command(self, args: str, character: Any) -> Dict[str, Any]:
        """Show character inventory."""
        if not character:
            return {'success': False, 'message': "No character data available."}
        
        if not character.inventory:
            return {'success': True, 'message': "Your inventory is empty."}
        
        return {
            'success': True,
            'message': "Inventory:\n- " + "\n- ".join(character.inventory)
        }
    
    def _stats_command(self, args: str, character: Any) -> Dict[str, Any]:
        """Show character stats."""
        if not character:
            return {'success': False, 'message': "No character data available."}
        
        stats_str = "\n".join([
            f"{stat}: {value} (Modifier: {character.stats.get_modifier(stat)})"
            for stat, value in character.stats.__dict__.items()
        ])
        
        return {
            'success': True,
            'message': f"Character: {character.name}, {character.class_name}, Level {character.level}\n\n{stats_str}"
        }
    
    def _look_command(self, args: str, character: Any) -> Dict[str, Any]:
        """Look around the current area."""
        # This is a placeholder - the actual implementation would depend on the game state
        return {
            'success': True,
            'message': "This command will be processed by the LLM to describe the current scene."
        }
    
    def _use_command(self, args: str, character: Any) -> Dict[str, Any]:
        """Use an item from inventory."""
        if not character:
            return {'success': False, 'message': "No character data available."}
        
        if not args:
            return {'success': False, 'message': "Specify an item to use."}
        
        if args not in character.inventory:
            return {'success': False, 'message': f"You don't have '{args}' in your inventory."}
        
        return {
            'success': True,
            'message': f"Using {args}. This action will be processed by the LLM."
        }

    def extract_roll_requests(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Extract roll requests from LLM response.
        
        Args:
            llm_response: The response from the LLM
            
        Returns:
            List of roll request dictionaries
        """
        # Look for patterns like [ROLL:skill_name]
        roll_pattern = r'\[ROLL:(\w+)\]'
        matches = re.finditer(roll_pattern, llm_response)
        
        roll_requests = []
        for match in matches:
            skill_name = match.group(1)
            roll_requests.append({
                'skill': skill_name,
                'pattern': match.group(0)  # The full match to replace later
            })
        
        return roll_requests

# TODO: Add support for more complex commands
# TODO: Add support for context-aware commands based on game state
# TODO: Add support for custom command aliases