"""
LLMClient Module

Handles all communication with the LM Studio API.
"""

import json
import requests
from typing import Dict, List, Any, Optional

class LLMClient:
    """
    Client for interacting with LM Studio's API.
    Handles formatting messages and sending requests to the LLM.
    """
    
    def __init__(self, api_url: str = "http://localhost:1234/v1/chat/completions"):
        """
        Initialize the LLM client.
        
        Args:
            api_url: URL for the LM Studio API endpoint
        """
        self.api_url = api_url
        
    def generate_response(self, 
                         messages: List[Dict[str, str]], 
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> Optional[str]:
        """
        Send a request to the LLM and get a response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The LLM's response text or None if there was an error
        """
        try:
            payload = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.api_url, 
                                    headers=headers,
                                    data=json.dumps(payload))
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    if "message" in result["choices"][0]:
                        return result["choices"][0]["message"]["content"]
                    elif "text" in result["choices"][0]:
                        return result["choices"][0]["text"]
                
                # If we couldn't extract the content using the expected structure,
                # print the full response for debugging
                print(f"Unexpected response structure: {result}")
                return "I'm sorry, I couldn't generate a proper response. Please try again."
            else:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response: {response.text}")
                return "I'm sorry, there was an error communicating with the language model. Please check the server logs."
                
        except Exception as e:
            print(f"Error communicating with LLM: {str(e)}")
            return "I'm sorry, there was an error communicating with the language model. Please check the server logs."
    
    def format_prompt(self,
                     player_input: str,
                     scene_context: str,
                     character_info: Dict[str, Any],
                     companion_notes: str = "",
                     history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """
        Format the prompt for the LLM using the template.
        
        Args:
            player_input: The player's current input text
            scene_context: Description of the current scene
            character_info: Character data dictionary
            companion_notes: Optional notes about companions
            history: Optional list of previous message dictionaries with "role" and "content" fields
            
        Returns:
            Formatted messages list ready for the LLM
        """
        # System message defines the AI's role and behavior
        system_message = {
            "role": "system",
            "content": (
                "You are the Dungeon Master. Interpret the player's input and continue the story. "
                "Consider their current situation and character traits. "
                "Stay in the tone of a gritty, mysterious fantasy world. "
                "When dice rolls are needed, indicate this with [ROLL:skill_name] but don't generate "
                "the results yourself."
            )
        }
        
        # Format character information as a string
        char_str = f"Character: {character_info['name']}, {character_info['class']}, Level {character_info['level']}\n"
        char_str += "Stats: " + ", ".join([f"{k}: {v}" for k, v in character_info['stats'].items()]) + "\n"
        
        # Create the user message with all context
        user_message = {
            "role": "user",
            "content": (
                f"Player input: {player_input}\n"
                f"Current scene: {scene_context}\n"
                f"{char_str}\n"
                f"Companion: {companion_notes}"
            )
        }
        
        # Construct the messages list
        messages = [system_message]
        
        # Add history if provided
        if history:
            # Only use the last 5 entries to avoid context overflow
            # history is already a list of message dictionaries with "role" and "content" fields
            messages.extend(history[-5:])
        
        messages.append(user_message)
        
        return messages

# TODO: Add streaming support for real-time responses
# TODO: Add fallback to other LLM providers
# TODO: Add caching for repeated queries