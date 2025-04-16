# Hollow Host - AI Dungeon Master Engine

Hollow Host is a modular solo/multiplayer text-based RPG system powered by a local LLM via LM Studio. The AI serves as the Dungeon Master (DM), enabling immersive tabletop-style RPGs through natural language, character systems, and rule-based gameplay.

## Features

- Natural language-based gameplay with an AI Dungeon Master
- Support for both solo and multiplayer gameplay (CLI and web interface)
- Modular architecture for easy expansion and customization
- Rule system agnostic, with ability to import or define rule sets
- Character, world, and campaign persistence
- Local-first AI model support via LM Studio

## Project Structure

```
hollow_host/
├── characters/         # Character-related functionality
├── docs/               # Documentation
├── examples/           # Example files and templates
├── llm/                # LLM client functionality
├── media/              # Media assets
├── narrative/          # Narrative-related functionality
├── rules/              # Game rules and mechanics
├── sessions/           # Game session management
├── templates/          # Templates for prompts
├── ui/                 # User interfaces (CLI and web)
├── world/              # World state and lore
├── main.py             # Main entry point
└── requirements.txt    # Dependencies
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hollow_host.git
   cd hollow_host
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure LM Studio is running locally with the API server enabled at http://localhost:1234/v1/chat

## Usage

### CLI Mode

Run the game in command-line interface mode:

```
python main.py
```

### Web Mode

Run the game as a web application:

```
python main.py --web
```

Then open your browser and navigate to http://localhost:8000

## Commands

- `/roll XdY+STAT` - Roll X dice with Y sides plus STAT modifier
- `/help` - Show help information
- `/inventory` - Show your inventory
- `/stats` - Show your character stats
- `/look` - Look around the current area
- `/use ITEM` - Use an item from your inventory
- `/quit` - Exit the game (CLI mode only)

## Development

### Core Modules

- **LLMClient**: Handles all communication with LM Studio
- **CommandParser**: Interprets roll, action, or narrative commands
- **Character**: Load/save JSON, apply modifiers
- **GameSession**: Handle current scene, logs, context state
- **NarrativeEngine**: Manages narrative generation and story progression
- **RulesEngine**: Handles game rules, dice rolling, and mechanics
- **UI**: Command-line and web interfaces

### Adding New Features

The modular architecture makes it easy to extend the system:

1. Add new commands in `rules/command_parser.py`
2. Add new game mechanics in `rules/engine.py`
3. Extend character capabilities in `characters/character.py`
4. Enhance narrative generation in `narrative/engine.py`

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses [LM Studio](https://lmstudio.ai/) for local LLM inference
- Inspired by tabletop RPGs and solo journaling games