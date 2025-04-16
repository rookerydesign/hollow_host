Phase 2: Rule Engine + Character Management
You are now building Phase 2 of the Hollow Host AI RPG Engine. This phase introduces custom character creation, importable rulesets, and a foundational turn-based combat system. Extend the existing modular architecture without breaking CLI or web compatibility.

🧱 1. Custom Character Builder
Goal: Enable users to create their own characters via the web portal or CLI.

Fields: name, class, level, stats (STR, DEX, etc.), skills, backstory

Use the existing Pydantic schema for validation

Include optional image upload or creation:

Stub: upload UI button or API endpoint (no processing logic yet)

Store filename/path in character record for future rendering

Deliverables:

characters/builder.py: logic for new character creation

Web route: /create-character form with input fields + upload image

CLI: guided prompts to generate and save a new character JSON

📄 2. Importable Rulesets
Goal: Allow players to bring their own game rules into the system.

Approach:

Define a ruleset template in YAML with:

Attribute-based skill checks (e.g. "stealth": "1d20 + DEX")

Combat rules (e.g. "attack": "1d20 + STR", "damage": "1d8 + weapon_bonus")

Special flags (e.g. "status_effects": { poisoned: {...} })

Option 1: Let users upload a ruleset.yaml through the web UI

Option 2: Provide a form-based ruleset editor to generate the YAML automatically

Deliverables:

rules/templates/base_rules.yaml: YAML template with comments

rules/loader.py: class that parses and validates rulesets

Web form: /ruleset-builder → structured fieldset → YAML file saved

Add file input to import ruleset.yaml manually

⚔️ 3. Turn-Based Combat Foundation
Goal: Scaffold a basic turn-based combat engine with initiative, action economy, and logic separation.

Use the provided reference document (“Core Structure of Turn-Based Combat”) to guide structure.

Combat Flow:

Initiative Roll (D20 + DEX or rule-defined modifier)

Turn Queue Management

Action Types: Attack, Move, Bonus, Reaction (stub logic OK)

Dice + Opposed Rolls: Evaluate based on rule system

Outcome Reporting: Success/fail state, damage, effects

Combat Log & Feedback: Update narrative + display roll data

Stub features for now:

Line of sight

Cover system

Grapples, overwatch, stances, terrain

Deliverables:

game/combat.py: CombatEngine class

rules/combat_logic.py: utilities for parsing and resolving combat actions

Web UI enhancements: combat phase indicators, roll summary display

