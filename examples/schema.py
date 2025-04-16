from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class CharacterStats(BaseModel):
    STR: int
    DEX: int
    INT: int
    CHA: int
    WIS: int
    CON: int

class CharacterSkills(BaseModel):
    stealth: Optional[int] = 0
    arcana: Optional[int] = 0
    persuasion: Optional[int] = 0

class CharacterModel(BaseModel):
    name: str
    class_name: str = Field(..., alias="class")
    level: int
    stats: CharacterStats
    skills: CharacterSkills
    abilities: List[str]
    status_effects: List[str]
    inventory: List[str]
    backstory: Optional[str]
