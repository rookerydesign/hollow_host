"""
CLI UI Module

Provides a command-line interface for the game.
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional, Callable

class CliUI:
    """
    Command-line interface for the game.
    """
    
    def __init__(self, width: int = 80):
        """
        Initialize the CLI UI.
        
        Args:
            width: Width of the terminal display
        """
        self.width = width
        self.colors_enabled = sys.platform != "win32" or os.environ.get("TERM") == "xterm"
    
    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system('cls' if sys.platform == 'win32' else 'clear')
    
    def print_header(self, title: str) -> None:
        """
        Print a header with the given title.
        
        Args:
            title: The header title
        """
        print("=" * self.width)
        print(title.center(self.width))
        print("=" * self.width)
    
    def print_divider(self) -> None:
        """Print a divider line."""
        print("-" * self.width)
    
    def print_scene(self, scene_text: str) -> None:
        """
        Print the scene description.
        
        Args:
            scene_text: The scene description text
        """
        self.print_divider()
        
        # Wrap text to fit within width
        words = scene_text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(" ".join(current_line + [word])) <= self.width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        for line in lines:
            print(line)
        
        self.print_divider()
    
    def print_character_info(self, character: Any) -> None:
        """
        Print character information.
        
        Args:
            character: Character object
        """
        print(f"Character: {character.name}, {character.class_name}, Level {character.level}")
        
        # Print stats
        stats_str = " | ".join([
            f"{stat}: {value} ({character.stats.get_modifier(stat):+d})"
            for stat, value in character.stats.__dict__.items()
        ])
        print(f"Stats: {stats_str}")
        
        # Print status effects if any
        if character.status_effects:
            effects_str = ", ".join(character.status_effects)
            print(f"Status Effects: {effects_str}")
    
    def print_inventory(self, character: Any) -> None:
        """
        Print character inventory.
        
        Args:
            character: Character object
        """
        print("Inventory:")
        if not character.inventory:
            print("  (empty)")
        else:
            for item in character.inventory:
                print(f"  - {item}")
    
    def print_help(self) -> None:
        """Print help information."""
        commands = [
            ("/roll XdY+STAT", "Roll X dice with Y sides plus STAT modifier"),
            ("/help", "Show this help message"),
            ("/inventory", "Show your inventory"),
            ("/stats", "Show your character stats"),
            ("/look", "Look around the current area"),
            ("/use ITEM", "Use an item from your inventory"),
            ("/quit", "Exit the game")
        ]
        
        print("Available Commands:")
        for cmd, desc in commands:
            print(f"  {cmd.ljust(20)} - {desc}")
    
    def print_roll_result(self, roll_data: Dict[str, Any]) -> None:
        """
        Print dice roll result.
        
        Args:
            roll_data: Dictionary containing roll result data
        """
        dice_str = f"{len(roll_data['rolls'])}d{roll_data['dice_type']}"
        rolls_str = ", ".join(str(r) for r in roll_data['rolls'])
        
        result = f"🎲 Rolling {dice_str}: [{rolls_str}] = {sum(roll_data['rolls'])}"
        
        if roll_data.get('modifier_name'):
            result += f" + {roll_data['modifier_name']} ({roll_data['modifier_value']})"
            result += f" = {roll_data['total']}"
        
        print(result)
    
    def print_dm_response(self, response: str) -> None:
        """
        Print the DM's response with typing effect.
        
        Args:
            response: The DM's response text
        """
        self.print_divider()
        
        # Split into paragraphs
        paragraphs = response.split("\n\n")
        
        for i, paragraph in enumerate(paragraphs):
            if i > 0:
                print()  # Add space between paragraphs
            
            # Typing effect (can be disabled for testing)
            for char in paragraph:
                print(char, end="", flush=True)
                time.sleep(0.01)  # Adjust speed as needed
            
            print()  # New line at end of paragraph
        
        self.print_divider()
    
    def get_player_input(self, prompt: str = "> ") -> str:
        """
        Get input from the player.
        
        Args:
            prompt: The input prompt
            
        Returns:
            The player's input text
        """
        return input(prompt)
    
    def print_error(self, message: str) -> None:
        """
        Print an error message.
        
        Args:
            message: The error message
        """
        if self.colors_enabled:
            print(f"\033[91mError: {message}\033[0m")
        else:
            print(f"Error: {message}")
    
    def print_success(self, message: str) -> None:
        """
        Print a success message.
        
        Args:
            message: The success message
        """
        if self.colors_enabled:
            print(f"\033[92m{message}\033[0m")
        else:
            print(message)
    
    def print_warning(self, message: str) -> None:
        """
        Print a warning message.
        
        Args:
            message: The warning message
        """
        if self.colors_enabled:
            print(f"\033[93m{message}\033[0m")
        else:
            print(f"Warning: {message}")
    
    def print_loading(self, message: str = "Thinking...") -> None:
        """
        Print a loading message.
        
        Args:
            message: The loading message
        """
        print(f"{message}", end="", flush=True)
    
    def update_loading(self, char: str = ".") -> None:
        """
        Update the loading indicator.
        
        Args:
            char: Character to append to the loading message
        """
        print(char, end="", flush=True)
    
    def end_loading(self) -> None:
        """End the loading indicator."""
        print()  # New line
    
    def confirm(self, message: str) -> bool:
        """
        Ask for confirmation.
        
        Args:
            message: The confirmation message
            
        Returns:
            True if confirmed, False otherwise
        """
        response = input(f"{message} (y/n): ").lower()
        return response in ["y", "yes"]
    
    def select_option(self, prompt: str, options: List[str]) -> int:
        """
        Present a list of options and get the user's selection.
        
        Args:
            prompt: The selection prompt
            options: List of option strings
            
        Returns:
            Index of the selected option
        """
        print(prompt)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        while True:
            try:
                choice = int(input("Enter your choice (number): "))
                if 1 <= choice <= len(options):
                    return choice - 1
                else:
                    print(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                print("Please enter a valid number")

# TODO: Add support for more advanced terminal features like cursor movement
# TODO: Add support for color themes
# TODO: Add support for ASCII art and simple animations