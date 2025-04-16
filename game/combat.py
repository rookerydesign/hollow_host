"""
Combat Engine Module

Handles turn-based combat mechanics, initiative tracking, and action resolution.
"""

import random
from typing import Dict, List, Any, Optional, Tuple
from characters.character import Character

class CombatParticipant:
    """
    Represents a participant in combat (player character or NPC).
    """
    
    def __init__(self, name: str, initiative: int, is_player: bool = False, 
                character: Optional[Character] = None, stats: Optional[Dict[str, int]] = None):
        """
        Initialize a combat participant.
        
        Args:
            name: The participant's name
            initiative: Initiative roll result
            is_player: Whether this is a player character
            character: Optional Character object for player characters
            stats: Optional stats dictionary for NPCs
        """
        self.name = name
        self.initiative = initiative
        self.is_player = is_player
        self.character = character
        self.stats = stats or {}
        self.current_hp = self.get_max_hp()
        self.has_acted = False
        self.has_moved = False
        self.has_bonus_action = False
        self.has_reaction = True
        self.status_effects = []
        
    def get_max_hp(self) -> int:
        """Get the participant's maximum HP."""
        if self.character:
            # For player characters, calculate based on class, level, and CON
            base_hp = 10  # Default base HP
            con_mod = self.character.stats.get_modifier("CON")
            level_bonus = (self.character.level - 1) * (5 + con_mod)  # 5 HP + CON mod per level after 1st
            return base_hp + con_mod + level_bonus
        else:
            # For NPCs, use provided stats or default
            return self.stats.get("hp", 10)
    
    def reset_turn(self) -> None:
        """Reset action flags for a new turn."""
        self.has_acted = False
        self.has_moved = False
        self.has_bonus_action = False
        self.has_reaction = True
    
    def take_damage(self, amount: int) -> int:
        """
        Apply damage to the participant.
        
        Args:
            amount: Amount of damage to apply
            
        Returns:
            The actual amount of damage taken
        """
        # Apply damage reduction from armor, resistances, etc. (simplified)
        actual_damage = max(1, amount)  # Minimum 1 damage
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal the participant.
        
        Args:
            amount: Amount of healing to apply
            
        Returns:
            The actual amount healed
        """
        max_hp = self.get_max_hp()
        old_hp = self.current_hp
        self.current_hp = min(max_hp, self.current_hp + amount)
        return self.current_hp - old_hp
    
    def is_alive(self) -> bool:
        """Check if the participant is alive."""
        return self.current_hp > 0
    
    def add_status_effect(self, effect: str, duration: int = 1) -> None:
        """
        Add a status effect to the participant.
        
        Args:
            effect: The effect name
            duration: Number of turns the effect lasts
        """
        self.status_effects.append({"name": effect, "duration": duration})
    
    def update_status_effects(self) -> List[str]:
        """
        Update status effects at the start of the participant's turn.
        
        Returns:
            List of expired effect names
        """
        expired = []
        remaining = []
        
        for effect in self.status_effects:
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                expired.append(effect["name"])
            else:
                remaining.append(effect)
        
        self.status_effects = remaining
        return expired

class CombatEngine:
    """
    Engine for managing turn-based combat.
    """
    
    def __init__(self, ruleset: Any = None):
        """
        Initialize the combat engine.
        
        Args:
            ruleset: Optional ruleset object for combat rules
        """
        self.ruleset = ruleset
        self.participants = []
        self.current_round = 0
        self.current_turn_index = 0
        self.combat_log = []
        self.is_active = False
    
    def start_combat(self, player_characters: List[Character], 
                    npcs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Start a combat encounter.
        
        Args:
            player_characters: List of player Character objects
            npcs: List of NPC dictionaries with name, stats, etc.
            
        Returns:
            Dictionary with combat initialization info
        """
        self.participants = []
        self.combat_log = []
        self.current_round = 1
        self.current_turn_index = 0
        
        # Add player characters
        for pc in player_characters:
            # Roll initiative for the player
            initiative_roll = self._roll_initiative(pc)
            self.participants.append(CombatParticipant(
                name=pc.name,
                initiative=initiative_roll,
                is_player=True,
                character=pc
            ))
            
            self.combat_log.append(f"{pc.name} rolls {initiative_roll} for initiative.")
        
        # Add NPCs
        for npc in npcs:
            # Roll initiative for the NPC
            initiative_roll = self._roll_initiative_npc(npc)
            self.participants.append(CombatParticipant(
                name=npc["name"],
                initiative=initiative_roll,
                is_player=False,
                stats=npc.get("stats", {})
            ))
            
            self.combat_log.append(f"{npc['name']} rolls {initiative_roll} for initiative.")
        
        # Sort participants by initiative (highest first)
        self.participants.sort(key=lambda p: p.initiative, reverse=True)
        
        # Set combat as active
        self.is_active = True
        
        # Create turn order message
        turn_order = [f"{i+1}. {p.name} ({p.initiative})" for i, p in enumerate(self.participants)]
        self.combat_log.append(f"Combat begins! Turn order:\n" + "\n".join(turn_order))
        
        return {
            "round": self.current_round,
            "turn_order": turn_order,
            "current_turn": self.get_current_participant().name if self.participants else None,
            "log": self.combat_log
        }
    
    def _roll_initiative(self, character: Character) -> int:
        """
        Roll initiative for a character.
        
        Args:
            character: Character object
            
        Returns:
            Initiative roll result
        """
        # Default D&D-style: 1d20 + DEX modifier
        dex_mod = character.stats.get_modifier("DEX")
        
        # If ruleset is available, use its initiative formula
        if self.ruleset and hasattr(self.ruleset, "combat") and "initiative" in self.ruleset.combat:
            # This would use the ruleset's initiative formula
            # For now, just use the default
            pass
        
        return random.randint(1, 20) + dex_mod
    
    def _roll_initiative_npc(self, npc: Dict[str, Any]) -> int:
        """
        Roll initiative for an NPC.
        
        Args:
            npc: NPC dictionary
            
        Returns:
            Initiative roll result
        """
        # Get DEX modifier from NPC stats or default to 0
        dex_mod = 0
        if "stats" in npc and "DEX" in npc["stats"]:
            dex_value = npc["stats"]["DEX"]
            dex_mod = (dex_value - 10) // 2
        
        return random.randint(1, 20) + dex_mod
    
    def get_current_participant(self) -> Optional[CombatParticipant]:
        """
        Get the participant whose turn it currently is.
        
        Returns:
            The current participant or None if combat is not active
        """
        if not self.is_active or not self.participants:
            return None
        
        return self.participants[self.current_turn_index]
    
    def next_turn(self) -> Dict[str, Any]:
        """
        Advance to the next turn in combat.
        
        Returns:
            Dictionary with updated combat state
        """
        if not self.is_active:
            return {"error": "Combat is not active"}
        
        # Move to next participant
        self.current_turn_index = (self.current_turn_index + 1) % len(self.participants)
        
        # If we've gone through all participants, start a new round
        if self.current_turn_index == 0:
            self.current_round += 1
            self.combat_log.append(f"Round {self.current_round} begins!")
            
            # Reset all participants' turn flags
            for participant in self.participants:
                participant.reset_turn()
        
        # Get the current participant
        current = self.get_current_participant()
        
        # Update status effects
        if current:
            expired_effects = current.update_status_effects()
            if expired_effects:
                effects_str = ", ".join(expired_effects)
                self.combat_log.append(f"{current.name} is no longer affected by: {effects_str}")
            
            self.combat_log.append(f"It's {current.name}'s turn.")
        
        return {
            "round": self.current_round,
            "current_turn": current.name if current else None,
            "is_player_turn": current.is_player if current else False,
            "log": self.combat_log[-5:]  # Return the last 5 log entries
        }
    
    def perform_attack(self, attacker_index: int, target_index: int, 
                      attack_type: str = "melee") -> Dict[str, Any]:
        """
        Perform an attack action.
        
        Args:
            attacker_index: Index of the attacking participant
            target_index: Index of the target participant
            attack_type: Type of attack (melee, ranged, spell)
            
        Returns:
            Dictionary with attack results
        """
        if not self.is_active:
            return {"error": "Combat is not active"}
        
        if attacker_index < 0 or attacker_index >= len(self.participants):
            return {"error": "Invalid attacker index"}
        
        if target_index < 0 or target_index >= len(self.participants):
            return {"error": "Invalid target index"}
        
        attacker = self.participants[attacker_index]
        target = self.participants[target_index]
        
        # Check if it's the attacker's turn
        current = self.get_current_participant()
        if current != attacker:
            return {"error": "It's not the attacker's turn"}
        
        # Check if the attacker has already acted
        if attacker.has_acted:
            return {"error": "Attacker has already used their action this turn"}
        
        # Roll attack
        attack_roll, attack_mod = self._roll_attack(attacker, attack_type)
        total_attack = attack_roll + attack_mod
        
        # Determine target's defense
        defense = self._get_defense(target)
        
        # Check if attack hits
        hit = total_attack >= defense
        
        # Log the attack attempt
        self.combat_log.append(
            f"{attacker.name} attacks {target.name} with a {attack_type} attack. "
            f"Rolls {attack_roll} + {attack_mod} = {total_attack} vs. defense {defense}. "
            f"{'Hit!' if hit else 'Miss!'}"
        )
        
        damage_dealt = 0
        if hit:
            # Roll damage
            damage_roll, damage_mod = self._roll_damage(attacker, attack_type)
            total_damage = damage_roll + damage_mod
            
            # Apply damage to target
            damage_dealt = target.take_damage(total_damage)
            
            # Log damage
            self.combat_log.append(
                f"{attacker.name} deals {damage_dealt} damage to {target.name}. "
                f"{target.name} has {target.current_hp} HP remaining."
            )
            
            # Check if target is defeated
            if not target.is_alive():
                self.combat_log.append(f"{target.name} is defeated!")
                
                # Remove defeated NPCs from combat
                if not target.is_player:
                    # Adjust current_turn_index if needed
                    if target_index < self.current_turn_index:
                        self.current_turn_index -= 1
                    
                    # Remove the target
                    self.participants.remove(target)
                    
                    # Check if combat should end
                    if self._check_combat_end():
                        self.end_combat()
        
        # Mark the attacker's action as used
        attacker.has_acted = True
        
        return {
            "hit": hit,
            "attack_roll": attack_roll,
            "attack_mod": attack_mod,
            "total_attack": total_attack,
            "defense": defense,
            "damage_dealt": damage_dealt,
            "target_hp": target.current_hp,
            "target_max_hp": target.get_max_hp(),
            "combat_active": self.is_active,
            "log": self.combat_log[-3:]  # Return the last 3 log entries
        }
    
    def _roll_attack(self, attacker: CombatParticipant, attack_type: str) -> Tuple[int, int]:
        """
        Roll an attack for a participant.
        
        Args:
            attacker: The attacking participant
            attack_type: Type of attack (melee, ranged, spell)
            
        Returns:
            Tuple of (roll, modifier)
        """
        roll = random.randint(1, 20)
        modifier = 0
        
        if attacker.is_player and attacker.character:
            # For player characters, use their stats
            if attack_type == "melee":
                modifier = attacker.character.stats.get_modifier("STR")
            elif attack_type == "ranged":
                modifier = attacker.character.stats.get_modifier("DEX")
            elif attack_type == "spell":
                modifier = attacker.character.stats.get_modifier("INT")
        else:
            # For NPCs, use their stats if available
            if "attack_bonus" in attacker.stats:
                modifier = attacker.stats["attack_bonus"]
        
        return roll, modifier
    
    def _roll_damage(self, attacker: CombatParticipant, attack_type: str) -> Tuple[int, int]:
        """
        Roll damage for an attack.
        
        Args:
            attacker: The attacking participant
            attack_type: Type of attack (melee, ranged, spell)
            
        Returns:
            Tuple of (roll, modifier)
        """
        # Default damage dice by attack type
        damage_dice = {
            "melee": (1, 6),  # 1d6
            "ranged": (1, 6),  # 1d6
            "spell": (1, 8)   # 1d8
        }
        
        num_dice, dice_type = damage_dice.get(attack_type, (1, 4))
        
        # Roll damage
        damage_roll = sum(random.randint(1, dice_type) for _ in range(num_dice))
        modifier = 0
        
        if attacker.is_player and attacker.character:
            # For player characters, use their stats
            if attack_type == "melee":
                modifier = attacker.character.stats.get_modifier("STR")
            elif attack_type == "ranged":
                modifier = attacker.character.stats.get_modifier("DEX")
            elif attack_type == "spell":
                modifier = attacker.character.stats.get_modifier("INT")
        else:
            # For NPCs, use their stats if available
            if "damage_bonus" in attacker.stats:
                modifier = attacker.stats["damage_bonus"]
        
        return damage_roll, modifier
    
    def _get_defense(self, target: CombatParticipant) -> int:
        """
        Get a participant's defense value.
        
        Args:
            target: The target participant
            
        Returns:
            Defense value
        """
        if target.is_player and target.character:
            # For player characters, calculate AC based on DEX
            base_ac = 10
            dex_mod = target.character.stats.get_modifier("DEX")
            # This is simplified - in a real game, armor would modify this
            return base_ac + dex_mod
        else:
            # For NPCs, use their stats if available
            return target.stats.get("defense", 10)
    
    def _check_combat_end(self) -> bool:
        """
        Check if combat should end.
        
        Returns:
            True if combat should end, False otherwise
        """
        # Count alive players and NPCs
        alive_players = sum(1 for p in self.participants if p.is_player and p.is_alive())
        alive_npcs = sum(1 for p in self.participants if not p.is_player and p.is_alive())
        
        # Combat ends if all players or all NPCs are defeated
        return alive_players == 0 or alive_npcs == 0
    
    def end_combat(self) -> Dict[str, Any]:
        """
        End the current combat encounter.
        
        Returns:
            Dictionary with combat results
        """
        if not self.is_active:
            return {"error": "Combat is not active"}
        
        # Determine the outcome
        alive_players = [p for p in self.participants if p.is_player and p.is_alive()]
        
        if alive_players:
            outcome = "victory"
            self.combat_log.append("Combat ends in victory for the players!")
        else:
            outcome = "defeat"
            self.combat_log.append("Combat ends in defeat for the players...")
        
        # Set combat as inactive
        self.is_active = False
        
        return {
            "outcome": outcome,
            "rounds": self.current_round,
            "survivors": [p.name for p in self.participants if p.is_alive()],
            "log": self.combat_log
        }
    
    def get_combat_state(self) -> Dict[str, Any]:
        """
        Get the current state of combat.
        
        Returns:
            Dictionary with combat state
        """
        if not self.is_active:
            return {"active": False}
        
        current = self.get_current_participant()
        
        return {
            "active": True,
            "round": self.current_round,
            "current_turn": current.name if current else None,
            "is_player_turn": current.is_player if current else False,
            "participants": [
                {
                    "name": p.name,
                    "is_player": p.is_player,
                    "initiative": p.initiative,
                    "hp": p.current_hp,
                    "max_hp": p.get_max_hp(),
                    "status_effects": [e["name"] for e in p.status_effects]
                }
                for p in self.participants
            ],
            "log": self.combat_log[-5:]  # Return the last 5 log entries
        }