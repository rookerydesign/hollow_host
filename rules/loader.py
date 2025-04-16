"""
Ruleset Loader Module

Handles loading, parsing, and validating game rulesets from YAML files.
"""

import os
import yaml
import re
from typing import Dict, Any, Optional, List, Tuple, Union
from pydantic import BaseModel, Field, validator

class DiceExpression(BaseModel):
    """Model for validating dice expressions like '2d6+3' or '1d20+DEX'"""
    expression: str
    
    @validator('expression')
    def validate_dice_expression(cls, v):
        # Basic regex for dice expressions like "2d6+3" or "1d20+DEX"
        pattern = r'^(\d+)d(\d+)(?:\s*[\+\-]\s*(\d+|\w+))?$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid dice expression: {v}")
        return v

class StatusEffect(BaseModel):
    """Model for status effects"""
    effect: str
    duration: str
    removal: Optional[str] = None

class CombatRules(BaseModel):
    """Model for combat rules"""
    initiative: str
    melee_attack: str
    ranged_attack: str
    spell_attack: str
    damage: Dict[str, str]
    defense: Dict[str, Any]
    actions: Dict[str, bool]
    critical: Dict[str, int]
    
    @validator('initiative', 'melee_attack', 'ranged_attack', 'spell_attack')
    def validate_attack_rolls(cls, v):
        DiceExpression(expression=v)
        return v
    
    @validator('damage')
    def validate_damage_rolls(cls, v):
        for weapon, expr in v.items():
            DiceExpression(expression=expr)
        return v

class Ruleset(BaseModel):
    """Model for a complete ruleset"""
    name: str
    description: str
    version: str
    checks: Dict[str, str]
    combat: CombatRules
    status_effects: Dict[str, StatusEffect]
    difficulty_classes: Dict[str, int]
    experience: Optional[Dict[str, Any]] = None
    custom_rules: Optional[Dict[str, Any]] = None
    
    @validator('checks')
    def validate_checks(cls, v):
        for skill, expr in v.items():
            DiceExpression(expression=expr)
        return v

class RulesetLoader:
    """
    Loader for game rulesets from YAML files.
    """
    
    def __init__(self, templates_dir: str = "rules/templates", 
                 custom_dir: str = "rules/custom"):
        """
        Initialize the ruleset loader.
        
        Args:
            templates_dir: Directory containing ruleset templates
            custom_dir: Directory for custom rulesets
        """
        self.templates_dir = templates_dir
        self.custom_dir = custom_dir
        
        # Create directories if they don't exist
        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(custom_dir, exist_ok=True)
    
    def load_ruleset(self, ruleset_path: str) -> Tuple[bool, str, Optional[Ruleset]]:
        """
        Load and validate a ruleset from a YAML file.
        
        Args:
            ruleset_path: Path to the ruleset YAML file
            
        Returns:
            Tuple of (success, message, ruleset)
        """
        if not os.path.exists(ruleset_path):
            return False, f"Ruleset file not found: {ruleset_path}", None
        
        try:
            # Load YAML file
            with open(ruleset_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Check if the file has the expected structure
            if not data or "ruleset" not in data:
                return False, "Invalid ruleset format: missing 'ruleset' key", None
            
            # Validate ruleset using Pydantic model
            ruleset = Ruleset(**data["ruleset"])
            
            return True, f"Ruleset '{ruleset.name}' loaded successfully.", ruleset
            
        except yaml.YAMLError as e:
            return False, f"Error parsing YAML: {str(e)}", None
        except Exception as e:
            return False, f"Error loading ruleset: {str(e)}", None
    
    def save_ruleset(self, ruleset: Ruleset, filepath: str) -> Tuple[bool, str]:
        """
        Save a ruleset to a YAML file.
        
        Args:
            ruleset: Ruleset object to save
            filepath: Path to save the ruleset
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Convert Pydantic model to dictionary
            ruleset_dict = {"ruleset": ruleset.dict()}
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save to YAML file
            with open(filepath, 'w') as f:
                yaml.dump(ruleset_dict, f, default_flow_style=False, sort_keys=False)
            
            return True, f"Ruleset '{ruleset.name}' saved successfully to {filepath}"
            
        except Exception as e:
            return False, f"Error saving ruleset: {str(e)}"
    
    def list_available_rulesets(self) -> List[Dict[str, str]]:
        """
        List all available rulesets (templates and custom).
        
        Returns:
            List of ruleset info dictionaries
        """
        rulesets = []
        
        # List template rulesets
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.templates_dir, filename)
                success, _, ruleset = self.load_ruleset(filepath)
                if success and ruleset:
                    rulesets.append({
                        "name": ruleset.name,
                        "description": ruleset.description,
                        "version": ruleset.version,
                        "filepath": filepath,
                        "type": "template"
                    })
        
        # List custom rulesets
        for filename in os.listdir(self.custom_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.custom_dir, filename)
                success, _, ruleset = self.load_ruleset(filepath)
                if success and ruleset:
                    rulesets.append({
                        "name": ruleset.name,
                        "description": ruleset.description,
                        "version": ruleset.version,
                        "filepath": filepath,
                        "type": "custom"
                    })
        
        return rulesets
    
    def create_ruleset_from_template(self, template_name: str, 
                                    custom_name: str, 
                                    modifications: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """
        Create a custom ruleset based on a template.
        
        Args:
            template_name: Name of the template ruleset
            custom_name: Name for the new custom ruleset
            modifications: Dictionary of modifications to apply
            
        Returns:
            Tuple of (success, message, filepath)
        """
        # Find template
        template_path = None
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.templates_dir, filename)
                success, _, ruleset = self.load_ruleset(filepath)
                if success and ruleset and ruleset.name == template_name:
                    template_path = filepath
                    break
        
        if not template_path:
            return False, f"Template ruleset '{template_name}' not found.", None
        
        # Load template
        success, message, template_ruleset = self.load_ruleset(template_path)
        if not success:
            return False, message, None
        
        # Apply modifications
        ruleset_dict = template_ruleset.dict()
        
        # Update basic info
        ruleset_dict["name"] = custom_name
        if "description" in modifications:
            ruleset_dict["description"] = modifications["description"]
        
        # Update checks
        if "checks" in modifications:
            for skill, expr in modifications["checks"].items():
                ruleset_dict["checks"][skill] = expr
        
        # Update combat rules
        if "combat" in modifications:
            for key, value in modifications["combat"].items():
                if key in ruleset_dict["combat"]:
                    if isinstance(value, dict) and isinstance(ruleset_dict["combat"][key], dict):
                        # Merge dictionaries
                        ruleset_dict["combat"][key].update(value)
                    else:
                        # Replace value
                        ruleset_dict["combat"][key] = value
        
        # Update status effects
        if "status_effects" in modifications:
            for effect, data in modifications["status_effects"].items():
                ruleset_dict["status_effects"][effect] = data
        
        # Update difficulty classes
        if "difficulty_classes" in modifications:
            for difficulty, value in modifications["difficulty_classes"].items():
                ruleset_dict["difficulty_classes"][difficulty] = value
        
        # Update experience rules
        if "experience" in modifications and "experience" in ruleset_dict:
            for key, value in modifications["experience"].items():
                if isinstance(value, dict) and isinstance(ruleset_dict["experience"].get(key, {}), dict):
                    # Merge dictionaries
                    ruleset_dict["experience"].setdefault(key, {}).update(value)
                else:
                    # Replace value
                    ruleset_dict["experience"][key] = value
        
        # Update custom rules
        if "custom_rules" in modifications:
            if "custom_rules" not in ruleset_dict:
                ruleset_dict["custom_rules"] = {}
            for rule, data in modifications["custom_rules"].items():
                ruleset_dict["custom_rules"][rule] = data
        
        # Create new ruleset
        try:
            new_ruleset = Ruleset(**ruleset_dict)
            
            # Save to file
            safe_name = custom_name.lower().replace(' ', '_')
            filepath = os.path.join(self.custom_dir, f"{safe_name}.yaml")
            
            success, message = self.save_ruleset(new_ruleset, filepath)
            if not success:
                return False, message, None
            
            return True, f"Custom ruleset '{custom_name}' created successfully.", filepath
            
        except Exception as e:
            return False, f"Error creating custom ruleset: {str(e)}", None
    
    def evaluate_dice_expression(self, expression: str, 
                               character: Optional[Any] = None) -> Tuple[int, List[int], int]:
        """
        Evaluate a dice expression like "2d6+3" or "1d20+DEX".
        
        Args:
            expression: Dice expression to evaluate
            character: Optional character object for stat modifiers
            
        Returns:
            Tuple of (total, dice_rolls, modifier)
        """
        import random
        
        # Parse the expression
        pattern = r'^(\d+)d(\d+)(?:\s*[\+\-]\s*(\d+|\w+))?$'
        match = re.match(pattern, expression)
        
        if not match:
            raise ValueError(f"Invalid dice expression: {expression}")
        
        num_dice = int(match.group(1))
        dice_type = int(match.group(2))
        modifier_str = match.group(3)
        
        # Roll the dice
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        base_total = sum(rolls)
        
        # Apply modifier if present
        modifier = 0
        if modifier_str:
            if modifier_str.isdigit():
                # Numeric modifier
                modifier = int(modifier_str)
            elif modifier_str.startswith('-') and modifier_str[1:].isdigit():
                # Negative numeric modifier
                modifier = -int(modifier_str[1:])
            elif character and hasattr(character.stats, modifier_str):
                # Stat modifier
                modifier = character.stats.get_modifier(modifier_str)
        
        total = base_total + modifier
        
        return total, rolls, modifier