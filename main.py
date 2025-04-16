"""
Hollow Host - AI Dungeon Master Engine

Main entry point for the application. Provides a command-line interface
for interacting with the AI Dungeon Master.
"""

import os
import json
import argparse
from typing import Dict, Any, Optional

from characters.character import Character, CharacterStats, CharacterSkills
from llm.client import LLMClient
from rules.command_parser import CommandParser
from sessions.game_session import GameSession

def create_default_character() -> Character:
    """
    Create a default character for testing.
    
    Returns:
        A default Character object
    """
    return Character(
        name="Thorne Ironheart",
        class_name="Warrior",
        level=1,
        stats=CharacterStats(
            STR=16,
            DEX=12,
            INT=10,
            CHA=8,
            WIS=14,
            CON=15
        ),
        skills=CharacterSkills(
            stealth=1,
            arcana=0,
            persuasion=0
        ),
        abilities=["Cleave", "Shield Block"],
        status_effects=[],
        inventory=["Rusty Sword", "Leather Armor", "Healing Potion", "Torch"],
        backstory="A former soldier seeking redemption for a past failure."
    )

def save_default_character() -> str:
    """
    Save the default character to a file.
    
    Returns:
        Path to the saved character file
    """
    character = create_default_character()
    
    # Create characters directory if it doesn't exist
    os.makedirs("characters/data", exist_ok=True)
    
    filepath = f"characters/data/{character.name.lower().replace(' ', '_')}.json"
    character.save_to_file(filepath)
    
    return filepath

def format_roll_result(roll_data: Dict[str, Any]) -> str:
    """
    Format a dice roll result for display.
    
    Args:
        roll_data: Dictionary containing roll result data
        
    Returns:
        Formatted string describing the roll result
    """
    dice_str = f"{len(roll_data['rolls'])}d{roll_data['dice_type']}"
    rolls_str = ", ".join(str(r) for r in roll_data['rolls'])
    
    result = f"🎲 Rolling {dice_str}: [{rolls_str}] = {sum(roll_data['rolls'])}"
    
    if roll_data['modifier_name']:
        result += f" + {roll_data['modifier_name']} ({roll_data['modifier_value']})"
        result += f" = {roll_data['total']}"
    
    return result

def process_llm_response(response: str, parser: CommandParser, character: Character) -> str:
    """
    Process the LLM response to handle any roll requests.
    
    Args:
        response: The response from the LLM
        parser: The command parser
        character: The character object
        
    Returns:
        The processed response with roll results
    """
    # Extract roll requests from the response
    roll_requests = parser.extract_roll_requests(response)
    
    # If no roll requests, return the original response
    if not roll_requests:
        return response
    
    # Process each roll request
    processed_response = response
    for request in roll_requests:
        skill = request['skill']
        pattern = request['pattern']
        
        # Determine the appropriate dice and modifier based on the skill
        dice_type = 20  # Default to d20 for skill checks
        num_dice = 1
        
        # Perform the roll
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        base_total = sum(rolls)
        
        # Apply modifier if it's a valid skill or stat
        modifier_value = 0
        if hasattr(character.stats, skill.upper()):
            modifier_value = character.stats.get_modifier(skill.upper())
        elif hasattr(character.skills, skill.lower()):
            modifier_value = character.get_skill_modifier(skill.lower())
        
        total = base_total + modifier_value
        
        # Format the roll result
        roll_result = f"[{skill.upper()} check: {base_total}"
        if modifier_value != 0:
            roll_result += f" + {modifier_value}"
        roll_result += f" = {total}]"
        
        # Replace the pattern with the roll result
        processed_response = processed_response.replace(pattern, roll_result)
    
    return processed_response

def run_cli_game():
    """Run the game in CLI mode."""
    print("=" * 80)
    print("Welcome to Hollow Host - AI Dungeon Master")
    print("=" * 80)
    
    # Initialize components
    llm_client = LLMClient()
    parser = CommandParser()
    
    # Check if default character exists, create if not
    character_path = "characters/data/thorne_ironheart.json"
    if not os.path.exists(character_path):
        character_path = save_default_character()
        print(f"Created default character at {character_path}")
    
    # Load character
    character = Character.load_from_file(character_path)
    print(f"Loaded character: {character.name}, {character.class_name}, Level {character.level}")
    
    # Create or load session
    session = GameSession(character=character)
    session.save()
    print(f"Started new session: {session.session_id}")
    print(f"Current location: {session.current_location}")
    print("\n" + session.scene_context + "\n")
    
    # Main game loop
    try:
        while True:
            # Get player input
            player_input = input("> ")
            
            if player_input.lower() in ['exit', 'quit', '/quit', '/exit']:
                break
            
            # Parse the input
            command_type, result = parser.parse(player_input, character)
            
            # Handle different command types
            if command_type == 'roll':
                # Display roll result
                print(format_roll_result(result))
                continue
            
            elif command_type == 'command':
                # Display command result
                print(result['message'])
                
                # If it's a command that should be processed by the LLM, continue
                if result.get('process_with_llm', False):
                    pass  # Continue to LLM processing
                else:
                    continue
            
            # For narrative input or commands that need LLM processing,
            # format the prompt and send to LLM
            messages = llm_client.format_prompt(
                player_input=player_input,
                scene_context=session.scene_context,
                character_info=character.model_dump(by_alias=True),
                history=session.get_formatted_history_for_llm()
            )
            
            # Get response from LLM
            dm_response = llm_client.generate_response(messages)
            
            if dm_response:
                # Process the response to handle any roll requests
                processed_response = process_llm_response(dm_response, parser, character)
                
                # Display the response
                print("\n" + processed_response + "\n")
                
                # Add to session history
                session.add_to_history(player_input, processed_response)
                
                # Update scene context (simplified - in a real implementation, 
                # we might extract this from the LLM response)
                session.update_scene_context(processed_response)
            else:
                print("\nError: Failed to get response from LLM. Please try again.\n")
    
    except KeyboardInterrupt:
        print("\nExiting game...")
    
    finally:
        # Save session and character state
        session.save()
        character.save_to_file(character_path)
        print(f"Session saved: {session.session_id}")
        print(f"Character saved: {character.name}")

def run_web_app():
    """Run the game as a web application."""
    # Import FastAPI components here to avoid dependencies if running CLI mode
    from fastapi import FastAPI
    import uvicorn
    from ui.web import WebUI
    
    # Create FastAPI app
    app = FastAPI(title="Hollow Host")
    
    # Initialize components
    llm_client = LLMClient()
    parser = CommandParser()
    
    # Check if default character exists, create if not
    character_path = "characters/data/thorne_ironheart.json"
    if not os.path.exists(character_path):
        character_path = save_default_character()
        print(f"Created default character at {character_path}")
    
    # Load character
    character = Character.load_from_file(character_path)
    
    # Create session
    session = GameSession(character=character)
    session.save()
    
    # Initialize WebUI with all routes and handlers
    web_ui = WebUI(
        app=app,
        llm_client=llm_client,
        command_parser=parser,
        character=character,
        game_session=session
    )
    
    # Run the app
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Hollow Host - AI Dungeon Master")
    parser.add_argument("--web", action="store_true", help="Run as web application")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run in appropriate mode
    if args.web:
        # Import required modules for web mode
        try:
            import fastapi
            import uvicorn
            import random  # For dice rolls
            run_web_app()
        except ImportError:
            print("Error: FastAPI or Uvicorn not installed. Please install with:")
            print("pip install fastapi uvicorn jinja2")
    else:
        # CLI mode
        import random  # For dice rolls
        run_cli_game()