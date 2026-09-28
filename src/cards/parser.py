import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CharacterCardV2Data(BaseModel):
    name: str
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_mes: str = ""
    mes_example: str = ""
    system_prompt: str = ""
    visual_tags: str = ""
    negative_prompt: str = ""
    post_history_instructions: str = ""
    alternate_greetings: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    creator: str = ""
    character_version: str = "1.0"


class CharacterCardV2(BaseModel):
    spec: str = "chara_card_v2"
    spec_version: str = "2.0"
    data: CharacterCardV2Data


def parse_character_card(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses either Tavern V2 format (spec: chara_card_v2) or legacy V1 flat format.
    Returns normalized dictionary ready for database insertion.
    """
    if "spec" in payload and payload.get("spec") == "chara_card_v2" and "data" in payload:
        data = payload["data"]
        return {
            "name": str(data.get("name", "Unnamed")).strip(),
            "tagline": str(data.get("creator_notes") or data.get("tags") or "")[:120],
            "avatar": str(data.get("avatar", "")),
            "description": str(data.get("description", "")).strip(),
            "personality": str(data.get("personality", "")).strip(),
            "scenario": str(data.get("scenario", "")).strip(),
            "first_message": str(data.get("first_mes", "")).strip(),
            "example_dialogue": str(data.get("mes_example", "")).strip(),
            "system_prompt": str(data.get("system_prompt", "")).strip(),
            "visual_tags": str(data.get("visual_tags", "")).strip(),
            "negative_prompt": str(data.get("negative_prompt", "")).strip(),
        }

    # Classic flat Tavern / V1 format
    return {
        "name": str(payload.get("name", payload.get("char_name", "Unnamed"))).strip(),
        "tagline": str(payload.get("tagline", payload.get("short_description", "")))[:120],
        "avatar": str(payload.get("avatar", "")),
        "description": str(payload.get("description", payload.get("char_persona", ""))).strip(),
        "personality": str(payload.get("personality", "")).strip(),
        "scenario": str(payload.get("scenario", payload.get("world_scenario", ""))).strip(),
        "first_message": str(payload.get("first_mes", payload.get("greeting", ""))).strip(),
        "example_dialogue": str(payload.get("mes_example", payload.get("example_dialogue", ""))).strip(),
        "system_prompt": str(payload.get("system_prompt", "")).strip(),
        "visual_tags": str(payload.get("visual_tags", "")).strip(),
        "negative_prompt": str(payload.get("negative_prompt", "")).strip(),
    }


def export_character_card_v2(char_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Exports normalized character attributes into official Tavern V2 JSON specification.
    """
    card = CharacterCardV2(
        spec="chara_card_v2",
        spec_version="2.0",
        data=CharacterCardV2Data(
            name=char_dict.get("name", "Unnamed"),
            description=char_dict.get("description", ""),
            personality=char_dict.get("personality", ""),
            scenario=char_dict.get("scenario", ""),
            first_mes=char_dict.get("first_message", ""),
            mes_example=char_dict.get("example_dialogue", ""),
            system_prompt=char_dict.get("system_prompt", ""),
            visual_tags=char_dict.get("visual_tags", ""),
            negative_prompt=char_dict.get("negative_prompt", ""),
            creator="Naughty-AI-Assistant",
            tags=["roleplay", "companion"],
        ),
    )
    return card.model_dump()
