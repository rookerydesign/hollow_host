# Product Requirements Document (PRD): AI Dungeon Master & Solo/Multiplayer RPG System

## 1. Overview
**Title:** AI Dungeon Master & Solo/Multiplayer RPG Campaign System  
**Purpose:** To create a modular, extensible RPG engine where an AI serves as the Dungeon Master (DM), enabling solo or multiplayer tabletop-style RPGs through natural language, character systems, and immersive media.  
**Target User:** Solo TTRPG players, narrative game designers, RPG enthusiasts, and potentially small RPG groups playing cooperatively online.

---

## 2. Goals and Non-Goals
### Goals:
- Natural language-based gameplay with an AI Dungeon Master (DM)
- Support for both solo and multiplayer gameplay
- Modular architecture for easy expansion and customization
- Rule system agnostic, with ability to import or define rule sets
- High immersion through pre-generated media: images, sound, and music
- Full character, world, and campaign persistence
- Local-first AI model support with fallback to online LLMs if needed

### Non-Goals:
- Real-time 3D graphics or physics simulation
- Initial support for mobile platforms (future consideration)

---

## 3. Use Cases
- **Solo Narrative Campaigns:** A single player explores an AI-driven RPG world with a persistent story.
- **Multiplayer Campaigns:** Two or more players share a story session, with AI managing the world and mechanics.
- **Custom System Campaigns:** A player uploads their own rules, story summary, and assets to run a fully custom RPG.
- **GM Bypass:** For groups without a human GM, the AI assumes the role and adapts dynamically.

---

## 4. System Features
### 4.1 Narrative Engine
- Local LLM integration (LM Studio via REST API)
- Personality and tone adjustment (gritty, heroic, etc.)
- Scene-based memory management with long-term story state tracking
- Autonomy mode for AI to introduce quests, lulls, or events

### 4.2 Game Logic Engine
- Modular rules system, defined as YAML/JSON or imported via plugin
- Dice rolling and rule adjudication
- Turn-based combat support and initiative tracking
- Skill checks, saving throws, and conditional logic parser

### 4.3 Character Management
- Character sheet editor with configurable attributes
- Companion AI personalities and decision trees
- Persistent stats, gear, status effects
- Character progression and level tracking

### 4.4 World State & Lore Engine
- Campaign/world save system
- Lore browser: NPCs, locations, factions, history
- NPC persistence within campaigns

### 4.5 Media Integration
- Pre-generated scene art using Forge + Stable Diffusion
- Real-time character portrait generation (optional)
- Audio engine for ambient loops and music (local folder or linked API)
- TTS integration via ElevenLabs or compatible local TTS
- Plugin-ready system for home automation triggers (e.g. lights, smart speakers)

### 4.6 Multiplayer Support
- Lobby system and session join logic
- Turn-based sync and lock-step progression
- Shared chat and optional voice comms integration (future)

### 4.7 Extensibility/Plugin Interface
- Plugin loader for:
  - New rule interpreters
  - Alternative UIs
  - Home automation extensions
- Custom campaign loader with metadata indexer
- Autotagger and prompt manager for media assets

---

## 5. Technical Architecture
### Core Stack
- **Backend:** Python 3.11+, FastAPI, Typer, Pydantic
- **Frontend (if web):** React, Vite, shadcn/ui or Chakra
- **Data Store:** PostgreSQL for structured data, Chroma/FAISS for vector memory
- **LLM:** LM Studio (local), optional OpenAI/OpenRouter fallback
- **Media:** Stable Diffusion (Forge), ElevenLabs, local sound folder
- **Storage:** File-based with metadata or object storage

### Core Modules
- NarrativeEngine
- GameRulesEngine
- CharacterManager
- WorldStateManager
- MediaManager
- SessionManager
- LLMClient
- PluginInterface

---

## 6. Development Phases
### Phase 1: Core Loop Prototype
- Local LLM text interaction
- Basic command parser and dice rolls
- Single character with hardcoded ruleset

### Phase 2: Rule Engine + Character Management
- Importable rulesets
- Custom character builder
- Turn-based combat and skill logic

### Phase 3: Campaign and World Persistence
- Save/load campaign and character state
- Lore and NPC persistence
- Session history

### Phase 4: Media Integration
- Scene pre-generation system and media tagging
- Audio playback engine
- Character portrait generation

### Phase 5: Multiplayer Core
- Session sync, user auth/local join
- Shared actions, turn locking, character control

### Phase 6: Extensibility & Plugin Framework
- Campaign/media import
- Plugin architecture
- Voice input/output options

### Phase 7: UX Enhancement & Story Experience Layer
- Context-aware prompt suggestions for players (e.g., "What do I see?")
- Profile and party cards showing character stats, inventory, traits
- Inventory sidebar with drag-and-drop logic or tooltip support
- Dynamic system feedback (e.g., color-coded roll outcomes, NPC emotions)
- Optional scene action menu (Fight/Hide/Use Item) for accessibility

---

## 7. MVP Specification
- Local LM Studio integration
- Terminal or basic web UI
- Single-player mode
- Basic rule interpreter (e.g. D20 + stat modifier)
- Scene and character prompt-to-image system
- Campaign save/load
- Companion AI behavior (stub logic)

---

## 8. Open Questions / Future Considerations
- How to balance narrative freedom with game rule enforcement
- Real-time collaboration in multiplayer (e.g. editing world state collaboratively)
- Asynchronous play model support
- Hosting campaigns for others (server/client split)

---

## Appendix A: Modular System Diagram