"""
Web UI Module

Provides a FastAPI-based web interface for the game.
"""

from fastapi import FastAPI, Request, Form, Depends, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any, Optional

class WebUI:
    """
    Web interface for the game using FastAPI.
    """
    
    def __init__(self, app: FastAPI, llm_client=None, command_parser=None, character=None,
                 game_session=None, templates_dir: str = "ui/templates"):
        """
        Initialize the web UI.
        
        Args:
            app: FastAPI application instance
            llm_client: LLM client instance
            command_parser: Command parser instance
            character: Character instance
            game_session: Game session instance
            templates_dir: Directory containing Jinja2 templates
        """
        import os
        
        self.app = app
        self.templates = Jinja2Templates(directory=templates_dir)
        self.llm_client = llm_client
        self.command_parser = command_parser
        self.character = character
        self.game_session = game_session
        
        # Ensure static directories exist
        os.makedirs("ui/static/css", exist_ok=True)
        os.makedirs("ui/static/js", exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory="ui/static"), name="static")
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register FastAPI routes."""
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Render the home page."""
            return self.render_home(request)
        
        @self.app.get("/play", response_class=HTMLResponse)
        async def index(request: Request):
            """Render the main game page."""
            return self.render_index(request)
        
        @self.app.get("/combat", response_class=HTMLResponse)
        async def combat_page(request: Request):
            """Render the combat page."""
            return self.render_combat(request)
        
        @self.app.get("/campaigns", response_class=HTMLResponse)
        async def campaigns_page(request: Request):
            """Render the campaigns page."""
            return self.render_campaigns(request)
            
        @self.app.get("/characters", response_class=HTMLResponse)
        async def characters_page(request: Request):
            """Render the characters page."""
            return self.render_characters(request)
        
        @self.app.get("/create-campaign", response_class=HTMLResponse)
        async def create_campaign_page(request: Request):
            """Render the create campaign page."""
            return self.render_create_campaign(request)
        
        @self.app.post("/create-campaign")
        async def create_campaign(request: Request):
            """Process campaign creation form."""
            form_data = await request.form()
            return await self.process_create_campaign(request, form_data)
        
        @self.app.get("/import-campaign", response_class=HTMLResponse)
        async def import_campaign_page(request: Request):
            """Render the import campaign page."""
            return self.render_import_campaign(request)
        
        @self.app.post("/import-campaign")
        async def import_campaign(request: Request):
            """Process campaign import form."""
            form_data = await request.form()
            return await self.process_import_campaign(request, form_data)
        
        @self.app.get("/lore", response_class=HTMLResponse)
        async def lore_page(request: Request):
            """Render the lore journal page."""
            return self.render_lore(request)
        
        @self.app.get("/lore/create", response_class=HTMLResponse)
        async def create_lore_page(request: Request):
            """Render the create lore entry page."""
            return self.render_create_lore(request)
        
        @self.app.get("/lore/edit/{lore_id}", response_class=HTMLResponse)
        async def edit_lore_page(request: Request, lore_id: str):
            """Render the edit lore entry page."""
            return self.render_edit_lore(request, lore_id)
        
        @self.app.get("/sessions", response_class=HTMLResponse)
        async def sessions_page(request: Request):
            """Render the sessions log page."""
            return self.render_sessions(request)
        
        @self.app.get("/sessions/{session_id}", response_class=HTMLResponse)
        async def session_detail_page(request: Request, session_id: str):
            """Render the session detail page."""
            return self.render_session_detail(request, session_id)
        
        @self.app.get("/dev/save-diffs", response_class=HTMLResponse)
        async def save_diffs_page(request: Request):
            """Render the save file diffs page."""
            return self.render_dev_tools(request, "save-diffs")
        
        @self.app.get("/dev/export", response_class=HTMLResponse)
        async def export_page(request: Request):
            """Render the export tools page."""
            return self.render_dev_tools(request, "export")
        
        @self.app.get("/dev/import", response_class=HTMLResponse)
        async def import_page(request: Request):
            """Render the import tools page."""
            return self.render_dev_tools(request, "import")
        
        @self.app.get("/dev/state-viewer", response_class=HTMLResponse)
        async def state_viewer_page(request: Request):
            """Render the raw state viewer page."""
            return self.render_dev_tools(request, "state-viewer")
        
        @self.app.post("/start-combat")
        async def start_combat(request: Request):
            """Start a new combat encounter."""
            form_data = await request.form()
            return await self.process_start_combat(request, form_data)
        
        @self.app.post("/combat-action")
        async def combat_action(request: Request):
            """Process a combat action."""
            form_data = await request.form()
            return await self.process_combat_action(request, form_data)
        
        @self.app.get("/end-combat")
        async def end_combat(request: Request):
            """End the current combat encounter."""
            return self.process_end_combat(request)
        
        @self.app.get("/characters", response_class=HTMLResponse)
        async def characters_redirect(request: Request):
            """Redirect to characters page."""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/characters", status_code=301)
            
        @self.app.get("/character/{name}", response_class=HTMLResponse)
        async def character_detail(request: Request, name: str):
            """Render individual character page."""
            # Get list of available characters
            from characters.builder import CharacterBuilder
            builder = CharacterBuilder()
            characters = builder.list_characters()
            
            # Find the requested character
            character = None
            for char in characters:
                if char["name"].lower().replace(' ', '_') == name:
                    # Get full character object since we only have basic info
                    character = builder.get_character(char["name"])
                    break
            
            if not character:
                raise HTTPException(status_code=404, detail="Character not found")
            
            return self.render_character(request, character)
            
        @self.app.get("/help", response_class=HTMLResponse)
        async def help_page(request: Request):
            """Render the help page."""
            return self.render_help(request)
        
        @self.app.get("/create-character", response_class=HTMLResponse)
        async def create_character_page(request: Request):
            """Render the character creation page."""
            return self.render_create_character(request)
        
        @self.app.post("/create-character")
        async def create_character(
            request: Request,
            name: str = Form(...),
            class_name: str = Form(..., alias="class"),
            level: int = Form(1),
            backstory: Optional[str] = Form(None),
            abilities: str = Form(""),
            inventory: str = Form(""),
            character_image: Optional[UploadFile] = File(None)
        ):
            """Process character creation form."""
            return await self.process_character_creation(
                request, name, class_name, level, backstory,
                abilities, inventory, character_image
            )
        
        @self.app.get("/ruleset-builder", response_class=HTMLResponse)
        async def ruleset_builder_page(request: Request):
            """Render the ruleset builder page."""
            return self.render_ruleset_builder(request)
        
        @self.app.post("/create-ruleset")
        async def create_ruleset(request: Request):
            """Process ruleset creation form."""
            form_data = await request.form()
            return await self.process_ruleset_creation(request, form_data)
        
        @self.app.post("/upload-ruleset")
        async def upload_ruleset(
            request: Request,
            ruleset_file: UploadFile = File(...),
            ruleset_type: str = Form("custom")
        ):
            """Process ruleset upload."""
            return await self.process_ruleset_upload(request, ruleset_file, ruleset_type)
        
        @self.app.get("/view-ruleset/{filepath:path}", response_class=HTMLResponse)
        async def view_ruleset(request: Request, filepath: str):
            """View a ruleset."""
            return self.render_view_ruleset(request, filepath)
        
        @self.app.get("/download-ruleset/{filepath:path}")
        async def download_ruleset(filepath: str):
            """Download a ruleset file."""
            return self.download_ruleset_file(filepath)
        
        @self.app.get("/delete-ruleset/{filepath:path}")
        async def delete_ruleset(request: Request, filepath: str):
            """Delete a ruleset."""
            return self.delete_ruleset_file(request, filepath)

        @self.app.post("/send")
        async def send_message(player_input: str = Form(...)):
            """Process player input and return DM response."""
            if not self.llm_client or not self.command_parser:
                raise HTTPException(status_code=500, detail="LLM client or command parser not initialized")

            # Parse the input
            command_type, result = self.command_parser.parse(player_input, self.character)
            
            # Handle different command types
            if command_type == 'roll':
                return {"type": "roll", "result": result, "formatted": self.format_roll_result(result)}
            
            elif command_type == 'command':
                if not result.get('process_with_llm', False):
                    return {"type": "command", "result": result}
            
            # For narrative input or commands that need LLM processing,
            # format the prompt and send to LLM
            messages = self.llm_client.format_prompt(
                player_input=player_input,
                scene_context=self.game_session.scene_context,
                character_info=self.character.model_dump(by_alias=True),
                history=self.game_session.get_formatted_history_for_llm()
            )
            
            # Get response from LLM
            dm_response = self.llm_client.generate_response(messages)
            
            if dm_response:
                # Process the response to handle any roll requests
                processed_response = self.process_llm_response(dm_response)
                
                # Add to session history
                self.game_session.add_to_history(player_input, processed_response)
                
                # Update scene context
                self.game_session.update_scene_context(processed_response)
                
                return {"type": "narrative", "response": processed_response}
            else:
                raise HTTPException(status_code=500, detail="Failed to get response from LLM")

    def format_roll_result(self, roll_data: Dict[str, Any]) -> str:
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

    def process_llm_response(self, response: str) -> str:
        """
        Process the LLM response to handle any roll requests.
        
        Args:
            response: The response from the LLM
            
        Returns:
            The processed response with roll results
        """
        # Extract roll requests from the response
        roll_requests = self.command_parser.extract_roll_requests(response)
        
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
            import random
            rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
            base_total = sum(rolls)
            
            # Apply modifier if it's a valid skill or stat
            modifier_value = 0
            if hasattr(self.character.stats, skill.upper()):
                modifier_value = self.character.stats.get_modifier(skill.upper())
            elif hasattr(self.character.skills, skill.lower()):
                modifier_value = self.character.get_skill_modifier(skill.lower())
            
            total = base_total + modifier_value
            
            # Format the roll result
            roll_result = f"[{skill.upper()} check: {base_total}"
            if modifier_value != 0:
                roll_result += f" + {modifier_value}"
            roll_result += f" = {total}]"
            
            # Replace the pattern with the roll result
            processed_response = processed_response.replace(pattern, roll_result)
        
        return processed_response

    def render_home(self, request: Request) -> HTMLResponse:
        """
        Render the home page.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response
        """
        # Check if developer mode is active
        dev_mode = False
        
        # In a real implementation, this would be determined by a setting or environment variable
        # For now, we'll just set it to False
        
        return self.templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "dev_mode": dev_mode
            }
        )
    
    def render_campaigns(self, request: Request) -> HTMLResponse:
        """
        Render the campaigns page.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response
        """
        # Get list of available campaigns
        from world.persistence import SaveManager
        
        save_manager = SaveManager()
        campaigns = save_manager.list_campaigns()
        
        return self.templates.TemplateResponse(
            "campaigns.html",
            {
                "request": request,
                "campaigns": campaigns
            }
        )
    
    def render_create_campaign(self, request: Request, error: str = None) -> HTMLResponse:
        """
        Render the create campaign page.
        
        Args:
            request: FastAPI request object
            error: Optional error message
            
        Returns:
            HTML response
        """
        # Get list of available characters
        from characters.builder import CharacterBuilder
        
        builder = CharacterBuilder()
        characters = builder.list_characters()
        
        # Get list of available rulesets
        from rules.loader import RulesetLoader
        
        loader = RulesetLoader()
        rulesets = loader.list_available_rulesets()
        
        return self.templates.TemplateResponse(
            "create_campaign.html",
            {
                "request": request,
                "characters": characters,
                "rulesets": rulesets,
                "error": error
            }
        )
    
    async def process_create_campaign(self, request: Request, form_data: Dict) -> HTMLResponse:
        """
        Process campaign creation form.
        
        Args:
            request: FastAPI request object
            form_data: Form data dictionary
            
        Returns:
            HTML response (redirect or error page)
        """
        from world.persistence import SaveManager, WorldState
        from fastapi.responses import RedirectResponse
        import uuid
        
        try:
            # Extract form data
            campaign_name = form_data.get("campaign_name")
            campaign_description = form_data.get("campaign_description", "")
            starting_location = form_data.get("starting_location", "Town Square")
            ruleset = form_data.get("ruleset", "default")
            
            # Generate a unique campaign ID
            campaign_id = f"campaign_{uuid.uuid4().hex[:8]}"
            
            # Create world state
            world_state = WorldState(
                campaign_id=campaign_id,
                name=campaign_name
            )
            
            # Add starting location
            from world.persistence import WorldLocation
            
            starting_loc = WorldLocation(
                name=starting_location,
                description=f"You are at {starting_location}.",
                discovered=True
            )
            
            world_state.add_location(starting_loc)
            
            # Set world flags
            world_state.set_flag("description", campaign_description)
            world_state.set_flag("ruleset", ruleset)
            world_state.set_flag("current_location", starting_location)
            
            # Add initial characters if selected
            initial_characters = form_data.getlist("initial_characters")
            if initial_characters:
                from characters.builder import CharacterBuilder
                
                builder = CharacterBuilder()
                for char_name in initial_characters:
                    character = builder.get_character(char_name)
                    if character:
                        world_state.add_character(character)
            
            # Save the world state
            save_manager = SaveManager()
            save_manager.save_world_state(world_state)
            
            # Redirect to campaigns page
            return RedirectResponse(url="/campaigns", status_code=303)
            
        except Exception as e:
            return self.render_create_campaign(request, error=f"Error creating campaign: {str(e)}")
    
    def render_import_campaign(self, request: Request, error: str = None, success: str = None) -> HTMLResponse:
        """
        Render the import campaign page.
        
        Args:
            request: FastAPI request object
            error: Optional error message
            success: Optional success message
            
        Returns:
            HTML response
        """
        return self.templates.TemplateResponse(
            "import_campaign.html",
            {
                "request": request,
                "error": error,
                "success": success
            }
        )
    
    async def process_import_campaign(self, request: Request, form_data: Dict) -> HTMLResponse:
        """
        Process campaign import form.
        
        Args:
            request: FastAPI request object
            form_data: Form data dictionary
            
        Returns:
            HTML response (redirect or error page)
        """
        from world.persistence import SaveManager
        from fastapi.responses import RedirectResponse
        import tempfile
        import os
        
        try:
            # Get the uploaded file
            campaign_file = form_data.get("campaign_file")
            if not campaign_file:
                return self.render_import_campaign(request, error="No file uploaded")
            
            # Save the file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file.write(await campaign_file.read())
                temp_path = temp_file.name
            
            # Import the campaign
            save_manager = SaveManager()
            campaign_id = save_manager.import_campaign(temp_path)
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            # Redirect to campaigns page
            return RedirectResponse(url="/campaigns", status_code=303)
            
        except Exception as e:
            return self.render_import_campaign(request, error=f"Error importing campaign: {str(e)}")
    
    def render_lore(self, request: Request) -> HTMLResponse:
        """
        Render the lore journal page.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response
        """
        # Get lore elements
        from world.lore_manager import LoreManager, LoreType
        
        # For now, we'll use a default campaign ID
        # In a real implementation, this would be determined by the current campaign
        campaign_id = "default_campaign"
        
        lore_manager = LoreManager()
        
        # Get all lore elements
        lore_elements = []
        for lore_type in LoreType:
            elements = lore_manager.get_lore_by_type(campaign_id, lore_type)
            lore_elements.extend(elements)
        
        # Get all unique tags
        tags = set()
        for element in lore_elements:
            tags.update(element.tags)
        
        return self.templates.TemplateResponse(
            "lore.html",
            {
                "request": request,
                "lore_elements": lore_elements,
                "tags": sorted(list(tags))
            }
        )
    
    def render_create_lore(self, request: Request, error: str = None) -> HTMLResponse:
        """
        Render the create lore entry page.
        
        Args:
            request: FastAPI request object
            error: Optional error message
            
        Returns:
            HTML response
        """
        # This would be implemented in a real application
        # For now, we'll just return a placeholder
        return HTMLResponse(content="Create Lore Entry Page - Not Implemented")
    
    def render_edit_lore(self, request: Request, lore_id: str) -> HTMLResponse:
        """
        Render the edit lore entry page.
        
        Args:
            request: FastAPI request object
            lore_id: ID of the lore entry to edit
            
        Returns:
            HTML response
        """
        # This would be implemented in a real application
        # For now, we'll just return a placeholder
        return HTMLResponse(content=f"Edit Lore Entry Page - ID: {lore_id} - Not Implemented")
    
    def render_sessions(self, request: Request) -> HTMLResponse:
        """
        Render the sessions log page.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response
        """
        # Get list of available sessions
        from sessions.game_session import GameSession
        
        sessions = GameSession.list_sessions()
        
        return self.templates.TemplateResponse(
            "sessions.html",
            {
                "request": request,
                "sessions": sessions,
                "current_session": None,
                "history": []
            }
        )
    
    def render_session_detail(self, request: Request, session_id: str) -> HTMLResponse:
        """
        Render the session detail page.
        
        Args:
            request: FastAPI request object
            session_id: ID of the session to display
            
        Returns:
            HTML response
        """
        # Get list of available sessions
        from sessions.game_session import GameSession
        
        sessions = GameSession.list_sessions()
        
        # Get the requested session
        try:
            current_session = GameSession.load(session_id)
            history = current_session.history
        except Exception:
            current_session = None
            history = []
        
        return self.templates.TemplateResponse(
            "sessions.html",
            {
                "request": request,
                "sessions": sessions,
                "current_session": current_session,
                "history": history
            }
        )
    
    def render_dev_tools(self, request: Request, active_tab: str = "save-diffs") -> HTMLResponse:
        """
        Render the developer tools page.
        
        Args:
            request: FastAPI request object
            active_tab: The active tab to display
            
        Returns:
            HTML response
        """
        # Get list of available campaigns
        from world.persistence import SaveManager
        
        save_manager = SaveManager()
        campaigns = save_manager.list_campaigns()
        
        # Get list of available characters
        from characters.builder import CharacterBuilder
        
        builder = CharacterBuilder()
        characters = builder.list_characters()
        
        # Get list of available sessions
        from sessions.game_session import GameSession
        
        sessions = GameSession.list_sessions()
        
        return self.templates.TemplateResponse(
            "dev_tools.html",
            {
                "request": request,
                "active_tab": active_tab,
                "campaigns": campaigns,
                "characters": characters,
                "sessions": sessions
            }
        )
    
    def render_index(self, request: Request,
                    character: Any = None,
                    session: Any = None,
                    messages: List[Dict[str, Any]] = None) -> HTMLResponse:
        """
        Render the main game page.
        
        Args:
            request: FastAPI request object
            character: Optional character object
            session: Optional game session object
            messages: Optional list of message dictionaries
            
        Returns:
            HTML response
        """
        # Get list of available characters for sidebar
        from characters.builder import CharacterBuilder
        builder = CharacterBuilder()
        characters = builder.list_characters()
        
        return self.templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "character": character or self.character,  # Use instance character if none provided
                "session": session or self.game_session,  # Use instance session if none provided
                "messages": messages or [],
                "characters": characters  # Add characters list for sidebar
            }
        )
    
    def render_characters(self, request: Request) -> HTMLResponse:
        """
        Render the characters page.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response
        """
        # Get list of available characters
        from characters.builder import CharacterBuilder
        builder = CharacterBuilder()
        characters = builder.list_characters()
        
        return self.templates.TemplateResponse(
            "characters.html",
            {
                "request": request,
                "characters": characters
            }
        )
    
    def render_character(self, request: Request, character: Any = None) -> HTMLResponse:
        """
        Render the character page.
        
        Args:
            request: FastAPI request object
            character: Optional character object
            
        Returns:
            HTML response
        """
        # Get list of available characters
        from characters.builder import CharacterBuilder
        builder = CharacterBuilder()
        characters = builder.list_characters()
        
        return self.templates.TemplateResponse(
            "character.html",
            {
                "request": request,
                "character": character,
                "characters": characters
            }
        )
    
    def render_create_character(self, request: Request, error: str = None) -> HTMLResponse:
        """
        Render the character creation page.
        
        Args:
            request: FastAPI request object
            error: Optional error message
            
        Returns:
            HTML response
        """
        return self.templates.TemplateResponse(
            "create_character.html",
            {
                "request": request,
                "error": error
            }
        )
    
    async def process_character_creation(
        self, request: Request, name: str, class_name: str, level: int,
        backstory: Optional[str], abilities_str: str, inventory_str: str,
        character_image: Optional[UploadFile]
    ) -> HTMLResponse:
        """
        Process character creation form submission.
        
        Args:
            request: FastAPI request object
            name: Character name
            class_name: Character class
            level: Character level
            backstory: Character backstory
            abilities_str: Comma-separated abilities
            inventory_str: Comma-separated inventory items
            character_image: Optional character image file
            
        Returns:
            HTML response (redirect or error page)
        """
        from characters.builder import CharacterBuilder
        from fastapi.responses import RedirectResponse
        
        # Parse form data
        abilities = [a.strip() for a in abilities_str.split(",") if a.strip()]
        inventory = [i.strip() for i in inventory_str.split(",") if i.strip()]
        
        # Extract stats from form data
        form = await request.form()
        stats = {}
        for stat in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
            stat_key = f"stats.{stat}"
            if stat_key in form:
                try:
                    stats[stat] = int(form[stat_key])
                except ValueError:
                    stats[stat] = 10  # Default if invalid
            else:
                stats[stat] = 10  # Default if missing
        
        # Extract skills from form data
        skills = {}
        for skill in ["stealth", "arcana", "persuasion"]:
            skill_key = f"skills.{skill}"
            if skill_key in form:
                try:
                    skills[skill] = int(form[skill_key])
                except ValueError:
                    skills[skill] = 0  # Default if invalid
            else:
                skills[skill] = 0  # Default if missing
        
        # Create character data dictionary
        character_data = {
            "name": name,
            "class": class_name,
            "level": level,
            "stats": stats,
            "skills": skills,
            "abilities": abilities,
            "inventory": inventory,
            "backstory": backstory or "",
            "status_effects": []
        }
        
        # Create the character
        builder = CharacterBuilder()
        success, message, character = builder.create_character(character_data)
        
        if not success:
            return self.render_create_character(request, error=message)
        
        # Handle character image if provided
        if character_image and character:
            try:
                image_data = await character_image.read()
                if image_data:
                    # Get file extension
                    filename = character_image.filename
                    ext = filename.split(".")[-1] if "." in filename else "png"
                    
                    # Save the image
                    builder.save_character_image(character.name, image_data, ext)
            except Exception as e:
                print(f"Error saving character image: {str(e)}")
        
        # Redirect to character page
        return RedirectResponse(url="/character", status_code=303)
    
    def render_ruleset_builder(self, request: Request,
                              error: str = None,
                              success: str = None) -> HTMLResponse:
        """
        Render the ruleset builder page.
        
        Args:
            request: FastAPI request object
            error: Optional error message
            success: Optional success message
            
        Returns:
            HTML response
        """
        from rules.loader import RulesetLoader
        
        # Get available ruleset templates
        loader = RulesetLoader()
        rulesets = loader.list_available_rulesets()
        
        # Filter templates
        templates = [r for r in rulesets if r["type"] == "template"]
        
        return self.templates.TemplateResponse(
            "ruleset_builder.html",
            {
                "request": request,
                "error": error,
                "success": success,
                "templates": templates,
                "rulesets": rulesets
            }
        )
    
    async def process_ruleset_creation(self, request: Request, form_data: Dict) -> HTMLResponse:
        """
        Process ruleset creation form submission.
        
        Args:
            request: FastAPI request object
            form_data: Form data dictionary
            
        Returns:
            HTML response (redirect or error page)
        """
        from rules.loader import RulesetLoader, Ruleset, CombatRules, StatusEffect
        from fastapi.responses import RedirectResponse
        
        try:
            # Extract basic info
            name = form_data.get("name")
            description = form_data.get("description")
            version = form_data.get("version", "1.0")
            template_base = form_data.get("template_base", "base_rules")
            
            # Initialize ruleset loader
            loader = RulesetLoader()
            
            # Load template as base
            template_path = f"rules/templates/base_rules.yaml"
            if template_base != "base_rules":
                template_path = template_base
            
            success, message, template_ruleset = loader.load_ruleset(template_path)
            if not success:
                return self.render_ruleset_builder(request, error=f"Error loading template: {message}")
            
            # Prepare modifications
            modifications = {
                "name": name,
                "description": description,
                "version": version,
                "checks": {},
                "combat": {},
                "status_effects": {},
                "difficulty_classes": {}
            }
            
            # Extract skill checks
            for key, value in form_data.items():
                if key.startswith("checks."):
                    skill = key.split(".", 1)[1]
                    modifications["checks"][skill] = value
            
            # Extract combat rules
            for key, value in form_data.items():
                if key.startswith("combat."):
                    parts = key.split(".", 1)
                    if len(parts) > 1:
                        combat_key = parts[1]
                        if "." in combat_key:
                            # Nested combat rule (e.g., combat.damage.unarmed)
                            category, subkey = combat_key.split(".", 1)
                            if category not in modifications["combat"]:
                                modifications["combat"][category] = {}
                            modifications["combat"][category][subkey] = value
                        else:
                            # Top-level combat rule (e.g., combat.initiative)
                            modifications["combat"][combat_key] = value
            
            # Extract status effects
            status_effects = {}
            for key, value in form_data.items():
                if key.startswith("status_effects["):
                    # Extract index and field from key like "status_effects[0].name"
                    parts = key.split("].", 1)
                    if len(parts) > 1:
                        index_str = parts[0].split("[")[1]
                        field = parts[1]
                        try:
                            index = int(index_str)
                            if index not in status_effects:
                                status_effects[index] = {}
                            status_effects[index][field] = value
                        except ValueError:
                            pass
            
            # Convert status effects to dictionary format
            for index, effect in status_effects.items():
                if "name" in effect and "effect" in effect and "duration" in effect:
                    name = effect["name"]
                    modifications["status_effects"][name] = {
                        "effect": effect["effect"],
                        "duration": effect["duration"],
                        "removal": effect.get("removal", "")
                    }
            
            # Extract difficulty classes
            for key, value in form_data.items():
                if key.startswith("difficulty_classes."):
                    dc_name = key.split(".", 1)[1]
                    try:
                        modifications["difficulty_classes"][dc_name] = int(value)
                    except ValueError:
                        pass
            
            # Create custom ruleset
            success, message, filepath = loader.create_ruleset_from_template(
                template_ruleset.name, name, modifications
            )
            
            if not success:
                return self.render_ruleset_builder(request, error=f"Error creating ruleset: {message}")
            
            return self.render_ruleset_builder(
                request,
                success=f"Ruleset '{name}' created successfully!"
            )
            
        except Exception as e:
            return self.render_ruleset_builder(request, error=f"Error: {str(e)}")
    
    async def process_ruleset_upload(self, request: Request,
                                   ruleset_file: UploadFile,
                                   ruleset_type: str) -> HTMLResponse:
        """
        Process ruleset file upload.
        
        Args:
            request: FastAPI request object
            ruleset_file: Uploaded ruleset file
            ruleset_type: Type of ruleset (custom or template)
            
        Returns:
            HTML response
        """
        from rules.loader import RulesetLoader, Ruleset
        import os
        import yaml
        
        try:
            # Read file content
            content = await ruleset_file.read()
            
            # Determine target directory
            target_dir = "rules/custom"
            if ruleset_type == "template":
                target_dir = "rules/templates"
            
            # Create directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Generate filename
            filename = ruleset_file.filename
            if not (filename.endswith(".yaml") or filename.endswith(".yml")):
                filename += ".yaml"
            
            filepath = os.path.join(target_dir, filename)
            
            # Write file
            with open(filepath, "wb") as f:
                f.write(content)
            
            # Validate ruleset
            loader = RulesetLoader()
            success, message, ruleset = loader.load_ruleset(filepath)
            
            if not success:
                # If validation fails, delete the file
                os.remove(filepath)
                return self.render_ruleset_builder(request, error=f"Invalid ruleset: {message}")
            
            return self.render_ruleset_builder(
                request,
                success=f"Ruleset '{ruleset.name}' uploaded successfully!"
            )
            
        except Exception as e:
            return self.render_ruleset_builder(request, error=f"Error uploading ruleset: {str(e)}")
    
    def render_view_ruleset(self, request: Request, filepath: str) -> HTMLResponse:
        """
        Render a page to view a ruleset.
        
        Args:
            request: FastAPI request object
            filepath: Path to the ruleset file
            
        Returns:
            HTML response
        """
        from rules.loader import RulesetLoader
        import yaml
        
        try:
            # Load ruleset
            loader = RulesetLoader()
            success, message, ruleset = loader.load_ruleset(filepath)
            
            if not success:
                return self.render_ruleset_builder(request, error=message)
            
            # Read raw YAML for display
            with open(filepath, "r") as f:
                yaml_content = f.read()
            
            return self.templates.TemplateResponse(
                "view_ruleset.html",
                {
                    "request": request,
                    "ruleset": ruleset,
                    "yaml_content": yaml_content,
                    "filepath": filepath
                }
            )
            
        except Exception as e:
            return self.render_ruleset_builder(request, error=f"Error viewing ruleset: {str(e)}")
    
    def download_ruleset_file(self, filepath: str):
        """
        Download a ruleset file.
        
        Args:
            filepath: Path to the ruleset file
            
        Returns:
            FileResponse
        """
        from fastapi.responses import FileResponse
        import os
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Ruleset file not found")
        
        return FileResponse(
            filepath,
            filename=os.path.basename(filepath),
            media_type="application/x-yaml"
        )
    
    def delete_ruleset_file(self, request: Request, filepath: str) -> HTMLResponse:
        """
        Delete a ruleset file.
        
        Args:
            request: FastAPI request object
            filepath: Path to the ruleset file
            
        Returns:
            HTML response (redirect)
        """
        from fastapi.responses import RedirectResponse
        import os
        
        try:
            if not os.path.exists(filepath):
                return self.render_ruleset_builder(request, error="Ruleset file not found")
            
            # Don't allow deleting base template
            if filepath == "rules/templates/base_rules.yaml":
                return self.render_ruleset_builder(
                    request,
                    error="Cannot delete the base ruleset template"
                )
            
            # Delete the file
            os.remove(filepath)
            
            return RedirectResponse(
                url="/ruleset-builder",
                status_code=303
            )
            
        except Exception as e:
            return self.render_ruleset_builder(request, error=f"Error deleting ruleset: {str(e)}")
    
    def render_help(self, request: Request) -> HTMLResponse:
        """
        Render the help page.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response
        """
        commands = [
            ("/roll XdY+STAT", "Roll X dice with Y sides plus STAT modifier"),
            ("/help", "Show this help page"),
            ("/inventory", "Show your inventory"),
            ("/stats", "Show your character stats"),
            ("/look", "Look around the current area"),
            ("/use ITEM", "Use an item from your inventory")
        ]
        
        return self.templates.TemplateResponse(
            "help.html",
            {
                "request": request,
                "commands": commands
            }
        )
    
    def render_combat(self, request: Request,
                     combat_state: Optional[Dict[str, Any]] = None,
                     error: Optional[str] = None) -> HTMLResponse:
        """
        Render the combat page.
        
        Args:
            request: FastAPI request object
            combat_state: Optional combat state dictionary
            error: Optional error message
            
        Returns:
            HTML response
        """
        # If no combat state is provided, check if there's an active combat
        if not combat_state:
            # In a real implementation, this would get the combat state from a session or database
            # For now, just provide a dummy inactive state
            combat_state = {"active": False}
        
        return self.templates.TemplateResponse(
            "combat.html",
            {
                "request": request,
                "combat_state": combat_state,
                "error": error
            }
        )
    
    async def process_start_combat(self, request: Request, form_data: Dict) -> HTMLResponse:
        """
        Process combat start form submission.
        
        Args:
            request: FastAPI request object
            form_data: Form data dictionary
            
        Returns:
            HTML response (redirect or error page)
        """
        from game.combat import CombatEngine
        from fastapi.responses import RedirectResponse
        import json
        
        try:
            # Extract enemies from form data
            enemies = []
            for key, value in form_data.items():
                if key.startswith("enemies[") and key.endswith("].name"):
                    # Extract index from key like "enemies[0].name"
                    index_str = key.split("[")[1].split("]")[0]
                    try:
                        index = int(index_str)
                        
                        # Get other enemy properties
                        name = value
                        hp = form_data.get(f"enemies[{index}].hp", "10")
                        defense = form_data.get(f"enemies[{index}].defense", "12")
                        
                        # Create enemy dictionary
                        enemy = {
                            "name": name,
                            "stats": {
                                "hp": int(hp),
                                "defense": int(defense),
                                "DEX": 10  # Default DEX for initiative
                            }
                        }
                        
                        enemies.append(enemy)
                    except ValueError:
                        pass
            
            # Get the player character
            from characters.builder import CharacterBuilder
            builder = CharacterBuilder()
            characters = builder.list_characters()
            
            if not characters:
                return self.render_combat(
                    request,
                    error="No player characters available. Please create a character first."
                )
            
            # Use the first character for now
            character_name = characters[0]["name"]
            character = builder.get_character(character_name)
            
            if not character:
                return self.render_combat(
                    request,
                    error=f"Character '{character_name}' not found."
                )
            
            # Initialize combat engine
            combat_engine = CombatEngine()
            
            # Start combat
            combat_state = combat_engine.start_combat([character], enemies)
            
            # In a real implementation, we would store the combat engine in a session
            # For now, just render the combat page with the initial state
            return self.render_combat(request, combat_state)
            
        except Exception as e:
            return self.render_combat(request, error=f"Error starting combat: {str(e)}")
    
    async def process_combat_action(self, request: Request, form_data: Dict) -> HTMLResponse:
        """
        Process a combat action.
        
        Args:
            request: FastAPI request object
            form_data: Form data dictionary
            
        Returns:
            HTML response
        """
        # In a real implementation, this would get the combat engine from a session
        # and process the action
        
        # For now, just render the combat page with a dummy state
        combat_state = {
            "active": True,
            "round": 1,
            "current_turn": "Player",
            "is_player_turn": True,
            "participants": [
                {
                    "name": "Player",
                    "is_player": True,
                    "initiative": 15,
                    "hp": 20,
                    "max_hp": 20,
                    "status_effects": []
                },
                {
                    "name": "Goblin",
                    "is_player": False,
                    "initiative": 12,
                    "hp": 7,
                    "max_hp": 7,
                    "status_effects": []
                }
            ],
            "log": [
                "Combat begins!",
                "Player rolls 15 for initiative.",
                "Goblin rolls 12 for initiative.",
                "It's Player's turn."
            ]
        }
        
        return self.render_combat(request, combat_state)
    
    def process_end_combat(self, request: Request) -> HTMLResponse:
        """
        End the current combat encounter.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response (redirect)
        """
        from fastapi.responses import RedirectResponse
        
        # In a real implementation, this would get the combat engine from a session
        # and end the combat
        
        # Redirect to the game page
        return RedirectResponse(url="/", status_code=303)
    
    def create_templates(self) -> None:
        """Create basic template files if they don't exist."""
        import os
        
        # Create templates directory if it doesn't exist
        os.makedirs("ui/templates", exist_ok=True)
        
        # Create static directory if it doesn't exist
        os.makedirs("ui/static/css", exist_ok=True)
        os.makedirs("ui/static/js", exist_ok=True)
        
        # Create index.html template
        index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hollow Host - AI Dungeon Master</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Hollow Host</h1>
            <nav>
                <ul>
                    <li><a href="/">Game</a></li>
                    <li><a href="/character">Character</a></li>
                    <li><a href="/help">Help</a></li>
                </ul>
            </nav>
        </header>
        
        <main>
            <div class="game-area">
                <div class="scene">
                    {% if session %}
                        <h2>{{ session.current_location }}</h2>
                        <p>{{ session.scene_context }}</p>
                    {% else %}
                        <h2>Welcome to Hollow Host</h2>
                        <p>Begin your adventure by typing a command below.</p>
                    {% endif %}
                </div>
                
                <div class="message-log">
                    {% for message in messages %}
                        <div class="message {% if message.type == 'player' %}player-message{% else %}dm-message{% endif %}">
                            <p>{{ message.content }}</p>
                        </div>
                    {% endfor %}
                </div>
                
                <div class="input-area">
                    <form id="command-form" action="/send" method="post">
                        <input type="text" id="player-input" name="player_input" placeholder="Enter your command or action..." autocomplete="off">
                        <button type="submit">Send</button>
                    </form>
                </div>
            </div>
            
            <aside class="sidebar">
                {% if character %}
                    <div class="character-summary">
                        <h3>{{ character.name }}</h3>
                        <p>{{ character.class_name }} - Level {{ character.level }}</p>
                        
                        <div class="stats">
                            {% for stat, value in character.stats.__dict__.items() %}
                                <div class="stat">
                                    <span class="stat-name">{{ stat }}</span>
                                    <span class="stat-value">{{ value }} ({{ character.stats.get_modifier(stat) }})</span>
                                </div>
                            {% endfor %}
                        </div>
                        
                        <div class="inventory-summary">
                            <h4>Inventory</h4>
                            <ul>
                                {% for item in character.inventory %}
                                    <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>
                {% endif %}
            </aside>
        </main>
        
        <footer>
            <p>Hollow Host - AI Dungeon Master Engine</p>
        </footer>
    </div>
    
    <script src="/static/js/main.js"></script>
</body>
</html>
        """
        
        # Create character.html template
        character_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Character - Hollow Host</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Hollow Host</h1>
            <nav>
                <ul>
                    <li><a href="/">Game</a></li>
                    <li><a href="/character">Character</a></li>
                    <li><a href="/help">Help</a></li>
                </ul>
            </nav>
        </header>
        
        <main>
            <div class="character-sheet">
                {% if character %}
                    <h2>{{ character.name }}</h2>
                    <p class="character-class">{{ character.class_name }} - Level {{ character.level }}</p>
                    
                    {% if character.backstory %}
                        <div class="backstory">
                            <h3>Backstory</h3>
                            <p>{{ character.backstory }}</p>
                        </div>
                    {% endif %}
                    
                    <div class="stats-section">
                        <h3>Stats</h3>
                        <div class="stats-grid">
                            {% for stat, value in character.stats.__dict__.items() %}
                                <div class="stat-box">
                                    <div class="stat-name">{{ stat }}</div>
                                    <div class="stat-value">{{ value }}</div>
                                    <div class="stat-modifier">{{ character.stats.get_modifier(stat) }}</div>
                                </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="skills-section">
                        <h3>Skills</h3>
                        <div class="skills-list">
                            {% for skill, value in character.skills.__dict__.items() %}
                                <div class="skill">
                                    <span class="skill-name">{{ skill }}</span>
                                    <span class="skill-value">{{ value }}</span>
                                </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="abilities-section">
                        <h3>Abilities</h3>
                        <ul class="abilities-list">
                            {% for ability in character.abilities %}
                                <li>{{ ability }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    
                    <div class="inventory-section">
                        <h3>Inventory</h3>
                        <ul class="inventory-list">
                            {% for item in character.inventory %}
                                <li>{{ item }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    
                    {% if character.status_effects %}
                        <div class="status-effects-section">
                            <h3>Status Effects</h3>
                            <ul class="status-effects-list">
                                {% for effect in character.status_effects %}
                                    <li>{{ effect }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                    {% endif %}
                {% else %}
                    <p>No character data available.</p>
                {% endif %}
            </div>
        </main>
        
        <footer>
            <p>Hollow Host - AI Dungeon Master Engine</p>
        </footer>
    </div>
</body>
</html>
        """
        
        # Create help.html template
        help_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Help - Hollow Host</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Hollow Host</h1>
            <nav>
                <ul>
                    <li><a href="/">Game</a></li>
                    <li><a href="/character">Character</a></li>
                    <li><a href="/help">Help</a></li>
                </ul>
            </nav>
        </header>
        
        <main>
            <div class="help-content">
                <h2>Game Help</h2>
                
                <section class="help-section">
                    <h3>Available Commands</h3>
                    <table class="commands-table">
                        <thead>
                            <tr>
                                <th>Command</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for command, description in commands %}
                                <tr>
                                    <td><code>{{ command }}</code></td>
                                    <td>{{ description }}</td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </section>
                
                <section class="help-section">
                    <h3>How to Play</h3>
                    <p>Hollow Host is an AI-powered text adventure game. You interact with the game by typing commands or actions, and the AI Dungeon Master responds with descriptions of what happens.</p>
                    <p>You can type natural language commands like "I search the room" or "I talk to the innkeeper", or use specific commands like "/roll" to perform dice rolls.</p>
                </section>
                
                <section class="help-section">
                    <h3>Dice Rolls</h3>
                    <p>To roll dice, use the <code>/roll</code> command followed by the dice notation. For example:</p>
                    <ul>
                        <li><code>/roll 1d20</code> - Roll a 20-sided die</li>
                        <li><code>/roll 2d6</code> - Roll two 6-sided dice</li>
                        <li><code>/roll 1d20+STR</code> - Roll a 20-sided die and add your Strength modifier</li>
                    </ul>
                </section>
            </div>
        </main>
        
        <footer>
            <p>Hollow Host - AI Dungeon Master Engine</p>
        </footer>
    </div>
</body>
</html>
        """
        
        # Create CSS file
        css = """
/* Basic Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

/* Header */
header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem;
    margin-bottom: 1rem;
}

header h1 {
    margin-bottom: 0.5rem;
}

nav ul {
    display: flex;
    list-style: none;
}

nav ul li {
    margin-right: 1rem;
}

nav ul li a {
    color: white;
    text-decoration: none;
}

nav ul li a:hover {
    text-decoration: underline;
}

/* Main Layout */
main {
    display: grid;
    grid-template-columns: 3fr 1fr;
    gap: 1rem;
}

/* Game Area */
.game-area {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 1rem;
    display: flex;
    flex-direction: column;
    height: 70vh;
}

.scene {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;
}

.message-log {
    flex-grow: 1;
    overflow-y: auto;
    margin-bottom: 1rem;
    padding: 0.5rem;
    background-color: #f9f9f9;
    border-radius: 3px;
}

.message {
    margin-bottom: 0.5rem;
    padding: 0.5rem;
    border-radius: 3px;
}

.player-message {
    background-color: #e8f4f8;
    text-align: right;
}

.dm-message {
    background-color: #f8f8f8;
}

.input-area {
    display: flex;
}

#command-form {
    display: flex;
    width: 100%;
}

#player-input {
    flex-grow: 1;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 3px;
    margin-right: 0.5rem;
}

button {
    padding: 0.5rem 1rem;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
}

button:hover {
    background-color: #2980b9;
}

/* Sidebar */
.sidebar {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 1rem;
}

.character-summary h3 {
    margin-bottom: 0.5rem;
}

.stats {
    margin: 1rem 0;
}

.stat {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}

.inventory-summary h4 {
    margin: 1rem 0 0.5rem;
}

.inventory-summary ul {
    list-style: none;
}

.inventory-summary li {
    margin-bottom: 0.25rem;
}

/* Character Sheet */
.character-sheet {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 1rem;
    grid-column: 1 / -1;
}

.character-class {
    color: #666;
    margin-bottom: 1rem;
}

.backstory {
    margin-bottom: 1.5rem;
    padding: 1rem;
    background-color: #f9f9f9;
    border-radius: 3px;
}

.stats-section, .skills-section, .abilities-section, .inventory-section, .status-effects-section {
    margin-bottom: 1.5rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
}

.stat-box {
    text-align: center;
    padding: 1rem;
    background-color: #f5f5f5;
    border-radius: 3px;
}

.stat-name {
    font-weight: bold;
}

.stat-value {
    font-size: 1.5rem;
    margin: 0.5rem 0;
}

.stat-modifier {
    color: #666;
}

.skills-list, .abilities-list, .inventory-list, .status-effects-list {
    list-style: none;
}

.skill {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}

/* Help Page */
.help-content {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 1rem;
    grid-column: 1 / -1;
}

.help-section {
    margin-bottom: 2rem;
}

.commands-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.commands-table th, .commands-table td {
    padding: 0.5rem;
    text-align: left;
    border-bottom: 1px solid #eee;
}

.commands-table th {
    background-color: #f5f5f5;
}

code {
    font-family: monospace;
    background-color: #f5f5f5;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
}

/* Footer */
footer {
    text-align: center;
    margin-top: 2rem;
    padding: 1rem;
    color: #666;
}

/* Responsive Design */
@media (max-width: 768px) {
    main {
        grid-template-columns: 1fr;
    }
    
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
        """
        
        # Create JavaScript file
        js = """
document.addEventListener('DOMContentLoaded', function() {
    const commandForm = document.getElementById('command-form');
    const playerInput = document.getElementById('player-input');
    const messageLog = document.querySelector('.message-log');
    
    if (commandForm) {
        commandForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const input = playerInput.value.trim();
            if (!input) return;
            
            // Add player message to log
            addMessage('player', input);
            
            // Clear input field
            playerInput.value = '';
            
            try {
                // Send command to server
                const response = await fetch('/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `player_input=${encodeURIComponent(input)}`
                });
                
                if (!response.ok) {
                    throw new Error('Failed to send command');
                }
                
                const data = await response.json();
                
                // Handle different response types
                if (data.type === 'narrative') {
                    addMessage('dm', data.response);
                } else if (data.type === 'roll') {
                    addMessage('dm', data.formatted);
                } else if (data.type === 'command') {
                    addMessage('dm', data.result.message);
                }
                
                // Scroll to bottom of message log
                messageLog.scrollTop = messageLog.scrollHeight;
                
            } catch (error) {
                console.error('Error:', error);
                addMessage('dm', 'Error: Failed to process command. Please try again.');
            }
        });
    }
    
    function addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const messagePara = document.createElement('p');
        messagePara.textContent = content;
        
        messageDiv.appendChild(messagePara);
        messageLog.appendChild(messageDiv);
        
        // Scroll to bottom
        messageLog.scrollTop = messageLog.scrollHeight;
    }
    
    // Auto-focus input field
    if (playerInput) {
        playerInput.focus();
    }
});
        """
        
        # Write files
        with open("ui/templates/index.html", "w") as f:
            f.write(index_html)
        
        with open("ui/templates/character.html", "w") as f:
            f.write(character_html)
        
        with open("ui/templates/help.html", "w") as f:
            f.write(help_html)
        
        with open("ui/static/css/style.css", "w") as f:
            f.write(css)
        
        with open("ui/static/js/main.js", "w") as f:
            f.write(js)

# TODO: Add support for WebSocket for real-time updates
# TODO: Add support for character creation/editing
# TODO: Add support for session management