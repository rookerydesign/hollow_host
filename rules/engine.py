"""
Rules Engine Module

Handles game rules, dice rolling, and mechanics.
"""

import random
import yaml
import os
from typing import Dict, List, Any, Optional, Tuple, Union

class RulesEngine:
    """
    Engine for handling game rules, dice rolling, and mechanics.
    """
    
    def __init__(self, ruleset_path: Optional[str] = None):
        """
        Initialize the rules engine.
        
        Args:
            ruleset_path: Optional path to a YAML ruleset file
        """
        self.ruleset = self._load_default_ruleset()
        
        if ruleset_path and os.path.exists(ruleset_path):
            self._load_ruleset(ruleset_path)
    
    def _load_default_ruleset(self) -> Dict[str, Any]:
        """
        Load the default ruleset.
        
        Returns:
            Default ruleset dictionary
        """
        return {
            "checks": {
                "stealth": "1d20 + DEX",
                "persuasion": "1d20 + CHA",
                "arcana": "1d20 + INT"
            },
            "combat": {
                "attack": "1d20 + STR",
                "damage": "1d8 + weapon_bonus"
            },
            "status_effects": {
                "poisoned": {
                    "effect": "-2 to all checks",
                    "duration": "3 turns"
                },
                "blessed": {
                    "effect": "+1 to attack rolls",
                    "duration": "until end of session"
                }
            }
        }
    
    def _load_ruleset(self, ruleset_path: str) -> None:
        """
        Load a ruleset from a YAML file.
        
        Args:
            ruleset_path: Path to the YAML ruleset file
        """
        try:
            with open(ruleset_path, 'r') as f:
                custom_ruleset = yaml.safe_load(f)
            
            if custom_ruleset and "ruleset" in custom_ruleset:
                # Merge with default ruleset
                for category, rules in custom_ruleset["ruleset"].items():
                    if category in self.ruleset:
                        self.ruleset[category].update(rules)
                    else:
                        self.ruleset[category] = rules
        except Exception as e:
            print(f"Error loading ruleset: {str(e)}")
    
    def roll_dice(self, dice_str: str) -> Tuple[int, List[int]]:
        """
        Roll dice based on a string specification (e.g., "2d6", "1d20+5").
        
        Args:
            dice_str: Dice specification string
            
        Returns:
            Tuple of (total, individual_rolls)
        """
        # Parse the dice string
        parts = dice_str.lower().replace(" ", "").split("+")
        
        dice_part = parts[0]
        modifier = 0
        
        # Extract modifier if present
        if len(parts) > 1:
            try:
                modifier = int(parts[1])
            except ValueError:
                # If not a number, it might be a stat reference (handled elsewhere)
                pass
        
        # Parse dice notation (e.g., "2d6")
        try:
            num_dice, dice_type = map(int, dice_part.split("d"))
        except ValueError:
            # Default to 1d20 if parsing fails
            num_dice, dice_type = 1, 20
        
        # Roll the dice
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        return total, rolls
    
    def check(self, check_type: str, character: Any) -> Dict[str, Any]:
        """
        Perform a skill or ability check.
        
        Args:
            check_type: The type of check to perform
            character: Character object with stats
            
        Returns:
            Dictionary with check results
        """
        if check_type not in self.ruleset["checks"]:
            return {
                "success": False,
                "message": f"Unknown check type: {check_type}"
            }
        
        check_formula = self.ruleset["checks"][check_type]
        
        # Parse the formula
        parts = check_formula.replace(" ", "").split("+")
        dice_part = parts[0]
        stat_part = parts[1] if len(parts) > 1 else None
        
        # Roll the dice
        num_dice, dice_type = map(int, dice_part.split("d"))
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        base_total = sum(rolls)
        
        # Apply stat modifier if present
        modifier = 0
        if stat_part and hasattr(character.stats, stat_part):
            modifier = character.stats.get_modifier(stat_part)
        
        # Apply status effect modifiers
        status_modifier = 0
        for status in character.status_effects:
            if status in self.ruleset["status_effects"]:
                effect = self.ruleset["status_effects"][status]["effect"]
                if "all checks" in effect:
                    # Extract the modifier value from the effect string
                    try:
                        mod_str = effect.split(" ")[0]
                        status_modifier += int(mod_str)
                    except (ValueError, IndexError):
                        pass
        
        total = base_total + modifier + status_modifier
        
        return {
            "success": True,
            "check_type": check_type,
            "rolls": rolls,
            "base_total": base_total,
            "stat": stat_part,
            "stat_modifier": modifier,
            "status_modifier": status_modifier,
            "total": total
        }
    
    def attack_roll(self, attacker: Any, target: Any = None, weapon: str = "default") -> Dict[str, Any]:
        """
        Perform an attack roll.
        
        Args:
            attacker: Character object making the attack
            target: Optional target character
            weapon: Weapon being used
            
        Returns:
            Dictionary with attack results
        """
        attack_formula = self.ruleset["combat"]["attack"]
        
        # Parse the formula
        parts = attack_formula.replace(" ", "").split("+")
        dice_part = parts[0]
        stat_part = parts[1] if len(parts) > 1 else "STR"
        
        # Roll the dice
        num_dice, dice_type = map(int, dice_part.split("d"))
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        base_total = sum(rolls)
        
        # Apply stat modifier
        modifier = 0
        if hasattr(attacker.stats, stat_part):
            modifier = attacker.stats.get_modifier(stat_part)
        
        # Apply status effect modifiers
        status_modifier = 0
        for status in attacker.status_effects:
            if status in self.ruleset["status_effects"]:
                effect = self.ruleset["status_effects"][status]["effect"]
                if "attack rolls" in effect:
                    # Extract the modifier value from the effect string
                    try:
                        mod_str = effect.split(" ")[0]
                        status_modifier += int(mod_str)
                    except (ValueError, IndexError):
                        pass
        
        total = base_total + modifier + status_modifier
        
        # Determine hit (simplified - would be more complex in a real implementation)
        hit = total >= 10  # Default difficulty
        
        return {
            "success": True,
            "rolls": rolls,
            "base_total": base_total,
            "stat": stat_part,
            "stat_modifier": modifier,
            "status_modifier": status_modifier,
            "total": total,
            "hit": hit
        }
    
    def damage_roll(self, attacker: Any, weapon: str = "default") -> Dict[str, Any]:
        """
        Perform a damage roll.
        
        Args:
            attacker: Character object making the attack
            weapon: Weapon being used
            
        Returns:
            Dictionary with damage results
        """
        damage_formula = self.ruleset["combat"]["damage"]
        
        # Parse the formula
        parts = damage_formula.replace(" ", "").split("+")
        dice_part = parts[0]
        bonus_part = parts[1] if len(parts) > 1 else None
        
        # Roll the dice
        num_dice, dice_type = map(int, dice_part.split("d"))
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        base_damage = sum(rolls)
        
        # Apply weapon bonus (simplified)
        weapon_bonus = 0
        if bonus_part == "weapon_bonus":
            # In a real implementation, this would look up the weapon's bonus
            weapon_bonus = 2  # Default bonus
        
        total_damage = base_damage + weapon_bonus
        
        return {
            "success": True,
            "rolls": rolls,
            "base_damage": base_damage,
            "weapon_bonus": weapon_bonus,
            "total_damage": total_damage
        }
    
    def apply_status_effect(self, target: Any, effect: str) -> Dict[str, Any]:
        """
        Apply a status effect to a character.
        
        Args:
            target: Character to apply the effect to
            effect: Status effect to apply
            
        Returns:
            Dictionary with result information
        """
        if effect not in self.ruleset["status_effects"]:
            return {
                "success": False,
                "message": f"Unknown status effect: {effect}"
            }
        
        target.apply_status_effect(effect)
        
        return {
            "success": True,
            "effect": effect,
            "description": self.ruleset["status_effects"][effect]["effect"],
            "duration": self.ruleset["status_effects"][effect]["duration"]
        }
    
    def remove_status_effect(self, target: Any, effect: str) -> Dict[str, Any]:
        """
        Remove a status effect from a character.
        
        Args:
            target: Character to remove the effect from
            effect: Status effect to remove
            
        Returns:
            Dictionary with result information
        """
        if effect not in target.status_effects:
            return {
                "success": False,
                "message": f"Character does not have status effect: {effect}"
            }
        
        target.remove_status_effect(effect)
        
        return {
            "success": True,
            "effect": effect,
            "message": f"Removed status effect: {effect}"
        }

# TODO: Add support for more complex combat mechanics
# TODO: Add support for initiative and turn order
# TODO: Add support for saving throws and resistances