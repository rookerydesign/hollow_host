"""
Combat Logic Module

Utilities for parsing and resolving combat actions based on the ruleset.
"""

import re
import random
from typing import Dict, List, Any, Optional, Tuple, Union

class CombatLogic:
    """
    Utilities for parsing and resolving combat actions.
    """
    
    def __init__(self, ruleset: Any = None):
        """
        Initialize the combat logic utilities.
        
        Args:
            ruleset: Optional ruleset object for combat rules
        """
        self.ruleset = ruleset
    
    def parse_action(self, action_text: str) -> Dict[str, Any]:
        """
        Parse a combat action from text.
        
        Args:
            action_text: The action text to parse
            
        Returns:
            Dictionary with parsed action details
        """
        # Define patterns for different action types
        attack_pattern = r'(?i)(?:attack|hit|strike|slash|shoot|cast|fire) (?:at )?(?:the )?(.+?)(?:with (.+))?$'
        move_pattern = r'(?i)(?:move|go|walk|run) (?:to|towards|away from) (.+)$'
        use_pattern = r'(?i)(?:use|drink|apply) (.+)$'
        
        # Check for attack actions
        attack_match = re.match(attack_pattern, action_text)
        if attack_match:
            target = attack_match.group(1).strip()
            weapon = attack_match.group(2).strip() if attack_match.group(2) else "default weapon"
            
            # Determine attack type based on weapon
            attack_type = self._determine_attack_type(weapon)
            
            return {
                "type": "attack",
                "target": target,
                "weapon": weapon,
                "attack_type": attack_type
            }
        
        # Check for movement actions
        move_match = re.match(move_pattern, action_text)
        if move_match:
            destination = move_match.group(1).strip()
            return {
                "type": "move",
                "destination": destination
            }
        
        # Check for item usage
        use_match = re.match(use_pattern, action_text)
        if use_match:
            item = use_match.group(1).strip()
            return {
                "type": "use",
                "item": item
            }
        
        # If no patterns match, treat as custom action
        return {
            "type": "custom",
            "text": action_text
        }
    
    def _determine_attack_type(self, weapon: str) -> str:
        """
        Determine the attack type based on the weapon.
        
        Args:
            weapon: The weapon name
            
        Returns:
            Attack type (melee, ranged, spell)
        """
        # List of common ranged weapons
        ranged_weapons = [
            "bow", "crossbow", "gun", "pistol", "rifle", "sling", "dart", "javelin", 
            "throwing", "thrown", "shoot", "fire"
        ]
        
        # List of common spell keywords
        spell_keywords = [
            "spell", "magic", "arcane", "divine", "cast", "fireball", "lightning", 
            "bolt", "ray", "beam", "blast", "orb", "wand", "staff"
        ]
        
        # Check if weapon contains ranged keywords
        if any(rw in weapon.lower() for rw in ranged_weapons):
            return "ranged"
        
        # Check if weapon contains spell keywords
        if any(sk in weapon.lower() for sk in spell_keywords):
            return "spell"
        
        # Default to melee
        return "melee"
    
    def resolve_skill_check(self, skill: str, difficulty: int, 
                           character: Any = None) -> Dict[str, Any]:
        """
        Resolve a skill check.
        
        Args:
            skill: The skill name
            difficulty: The difficulty class (DC)
            character: Optional character object
            
        Returns:
            Dictionary with skill check results
        """
        # Default to a basic d20 roll
        roll = random.randint(1, 20)
        modifier = 0
        
        # If character is provided, apply skill modifier
        if character:
            # Check if it's a stat check
            if skill.upper() in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
                modifier = character.stats.get_modifier(skill.upper())
            # Check if it's a skill check
            elif hasattr(character.skills, skill.lower()):
                modifier = character.get_skill_modifier(skill.lower())
        
        total = roll + modifier
        success = total >= difficulty
        
        return {
            "skill": skill,
            "roll": roll,
            "modifier": modifier,
            "total": total,
            "difficulty": difficulty,
            "success": success
        }
    
    def resolve_opposed_check(self, active_skill: str, active_character: Any,
                             passive_skill: str, passive_character: Any) -> Dict[str, Any]:
        """
        Resolve an opposed skill check.
        
        Args:
            active_skill: The active character's skill
            active_character: The active character
            passive_skill: The passive character's skill
            passive_character: The passive character
            
        Returns:
            Dictionary with opposed check results
        """
        # Roll for active character
        active_roll = random.randint(1, 20)
        active_mod = 0
        
        # Roll for passive character
        passive_roll = random.randint(1, 20)
        passive_mod = 0
        
        # Apply modifiers if characters are provided
        if active_character:
            if active_skill.upper() in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
                active_mod = active_character.stats.get_modifier(active_skill.upper())
            elif hasattr(active_character.skills, active_skill.lower()):
                active_mod = active_character.get_skill_modifier(active_skill.lower())
        
        if passive_character:
            if passive_skill.upper() in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
                passive_mod = passive_character.stats.get_modifier(passive_skill.upper())
            elif hasattr(passive_character.skills, passive_skill.lower()):
                passive_mod = passive_character.get_skill_modifier(passive_skill.lower())
        
        active_total = active_roll + active_mod
        passive_total = passive_roll + passive_mod
        
        success = active_total >= passive_total
        
        return {
            "active_skill": active_skill,
            "active_roll": active_roll,
            "active_mod": active_mod,
            "active_total": active_total,
            "passive_skill": passive_skill,
            "passive_roll": passive_roll,
            "passive_mod": passive_mod,
            "passive_total": passive_total,
            "success": success
        }
    
    def roll_dice(self, dice_str: str, character: Any = None) -> Dict[str, Any]:
        """
        Roll dice based on a dice string (e.g., "2d6+3" or "1d20+STR").
        
        Args:
            dice_str: The dice string to parse and roll
            character: Optional character object for stat modifiers
            
        Returns:
            Dictionary with dice roll results
        """
        # Parse the dice string
        pattern = r'^(\d+)d(\d+)(?:\s*[\+\-]\s*(\d+|\w+))?$'
        match = re.match(pattern, dice_str)
        
        if not match:
            return {"error": f"Invalid dice string: {dice_str}"}
        
        num_dice = int(match.group(1))
        dice_type = int(match.group(2))
        modifier_str = match.group(3)
        
        # Roll the dice
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        base_total = sum(rolls)
        
        # Apply modifier if present
        modifier = 0
        modifier_source = None
        
        if modifier_str:
            if modifier_str.isdigit():
                # Numeric modifier
                modifier = int(modifier_str)
                modifier_source = "fixed"
            elif modifier_str.startswith('-') and modifier_str[1:].isdigit():
                # Negative numeric modifier
                modifier = -int(modifier_str[1:])
                modifier_source = "fixed"
            elif character and hasattr(character.stats, modifier_str):
                # Stat modifier
                modifier = character.stats.get_modifier(modifier_str)
                modifier_source = f"{modifier_str} stat"
            elif character and hasattr(character.skills, modifier_str.lower()):
                # Skill modifier
                modifier = character.get_skill_modifier(modifier_str.lower())
                modifier_source = f"{modifier_str} skill"
        
        total = base_total + modifier
        
        return {
            "dice_str": dice_str,
            "num_dice": num_dice,
            "dice_type": dice_type,
            "rolls": rolls,
            "base_total": base_total,
            "modifier": modifier,
            "modifier_source": modifier_source,
            "total": total
        }
    
    def apply_ruleset_formula(self, formula_type: str, character: Any = None) -> Dict[str, Any]:
        """
        Apply a formula from the ruleset.
        
        Args:
            formula_type: The type of formula to apply (e.g., "initiative", "melee_attack")
            character: Optional character object
            
        Returns:
            Dictionary with formula results
        """
        if not self.ruleset:
            return {"error": "No ruleset provided"}
        
        # Check if the ruleset has combat rules
        if not hasattr(self.ruleset, "combat"):
            return {"error": "Ruleset does not have combat rules"}
        
        # Get the formula from the ruleset
        formula = None
        
        if formula_type == "initiative":
            formula = getattr(self.ruleset.combat, "initiative", "1d20+DEX")
        elif formula_type == "melee_attack":
            formula = getattr(self.ruleset.combat, "melee_attack", "1d20+STR")
        elif formula_type == "ranged_attack":
            formula = getattr(self.ruleset.combat, "ranged_attack", "1d20+DEX")
        elif formula_type == "spell_attack":
            formula = getattr(self.ruleset.combat, "spell_attack", "1d20+INT")
        elif formula_type.startswith("damage_"):
            weapon_type = formula_type[7:]  # Extract weapon type from "damage_weapon_type"
            if hasattr(self.ruleset.combat, "damage") and weapon_type in self.ruleset.combat.damage:
                formula = self.ruleset.combat.damage[weapon_type]
            else:
                formula = "1d6"  # Default damage
        
        if not formula:
            return {"error": f"Formula not found for {formula_type}"}
        
        # Roll the dice using the formula
        return self.roll_dice(formula, character)
    
    def format_roll_result(self, roll_result: Dict[str, Any]) -> str:
        """
        Format a roll result for display.
        
        Args:
            roll_result: Dictionary with roll results
            
        Returns:
            Formatted string describing the roll result
        """
        if "error" in roll_result:
            return f"Error: {roll_result['error']}"
        
        if "dice_str" in roll_result:
            # Format dice roll
            rolls_str = ", ".join(str(r) for r in roll_result["rolls"])
            result = f"🎲 Rolling {roll_result['dice_str']}: [{rolls_str}] = {roll_result['base_total']}"
            
            if roll_result["modifier"] != 0:
                mod_sign = "+" if roll_result["modifier"] > 0 else ""
                result += f" {mod_sign}{roll_result['modifier']}"
                if roll_result["modifier_source"]:
                    result += f" ({roll_result['modifier_source']})"
                result += f" = {roll_result['total']}"
            
            return result
        
        if "skill" in roll_result:
            # Format skill check
            result = f"🎲 {roll_result['skill']} check: {roll_result['roll']}"
            
            if roll_result["modifier"] != 0:
                mod_sign = "+" if roll_result["modifier"] > 0 else ""
                result += f" {mod_sign}{roll_result['modifier']}"
                result += f" = {roll_result['total']}"
            
            result += f" vs. DC {roll_result['difficulty']}"
            result += f" - {'Success!' if roll_result['success'] else 'Failure!'}"
            
            return result
        
        if "active_skill" in roll_result:
            # Format opposed check
            result = (f"🎲 Opposed check: {roll_result['active_skill']} "
                     f"({roll_result['active_roll']} + {roll_result['active_mod']} = {roll_result['active_total']}) "
                     f"vs. {roll_result['passive_skill']} "
                     f"({roll_result['passive_roll']} + {roll_result['passive_mod']} = {roll_result['passive_total']})")
            
            result += f" - {'Success!' if roll_result['success'] else 'Failure!'}"
            
            return result
        
        # Generic format for other roll types
        return f"Roll result: {roll_result}"