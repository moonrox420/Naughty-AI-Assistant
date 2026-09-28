import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.cards.parser import export_character_card_v2, parse_character_card
from src.cards.presets import seed_builtin_characters
from src.config import settings
from src.db.repository import (
    CharacterRecord,
    MemoryFactRecord,
    MessageRecord,
    Repository,
    SessionRecord,
    UserPersonaRecord,
)
from src.llm.detector import detect_all_runners

router = APIRouter(prefix="/api")


# --- Schemas ---
class CharacterCreate(BaseModel):
    name: str
    tagline: str = ""
    avatar: str = ""
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_message: str = ""
    example_dialogue: str = ""
    system_prompt: str = ""


class UserPersonaCreate(BaseModel):
    name: str
    pronouns: str = ""
    description: str = ""
    traits: str = ""
    is_active: int = 0


class TitleUpdate(BaseModel):
    title: str


class MemoryUpdate(BaseModel):
    memory_notes: str


class MessageContentUpdate(BaseModel):
    content: str


class MessageCreate(BaseModel):
    role: str
    content: str
    image_url: Optional[str] = ""


class SwipeSelect(BaseModel):
    swipe_index: int


class FactCreate(BaseModel):
    fact_text: str
    category: str = "general"


# --- Character Routes ---
@router.get("/characters", response_model=List[CharacterRecord])
async def list_characters():
    chars = await Repository.get_characters()
    if not chars:
        await seed_builtin_characters()
        chars = await Repository.get_characters()
    return chars


@router.get("/characters/{char_id}", response_model=CharacterRecord)
async def get_character(char_id: str):
    char = await Repository.get_character(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char


@router.post("/characters", response_model=CharacterRecord, status_code=status.HTTP_201_CREATED)
async def create_character(data: CharacterCreate):
    return await Repository.upsert_character(data.model_dump())


@router.put("/characters/{char_id}", response_model=CharacterRecord)
async def update_character(char_id: str, data: CharacterCreate):
    char_dict = data.model_dump()
    char_dict["id"] = char_id
    return await Repository.upsert_character(char_dict)


@router.delete("/characters/{char_id}")
async def delete_character(char_id: str):
    success = await Repository.delete_character(char_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"deleted": True, "id": char_id}


@router.post("/characters/import", response_model=CharacterRecord)
async def import_character_card(payload: Dict[str, Any]):
    parsed = parse_character_card(payload)
    if not parsed.get("name"):
        raise HTTPException(status_code=400, detail="Character name is missing")
    return await Repository.upsert_character(parsed)


@router.get("/characters/{char_id}/export")
async def export_character_card(char_id: str):
    char = await Repository.get_character(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    v2_data = export_character_card_v2(char.model_dump())
    return JSONResponse(
        content=v2_data,
        headers={"Content-Disposition": f'attachment; filename="{char.name}_v2.json"'},
    )


# --- User Persona Routes ---
@router.get("/user-personas", response_model=List[UserPersonaRecord])
async def list_user_personas():
    return await Repository.get_user_personas()


@router.post("/user-personas", response_model=UserPersonaRecord)
async def create_user_persona(data: UserPersonaCreate):
    return await Repository.upsert_user_persona(data.model_dump())


@router.put("/user-personas/{persona_id}", response_model=UserPersonaRecord)
async def update_user_persona(persona_id: str, data: UserPersonaCreate):
    d = data.model_dump()
    d["id"] = persona_id
    return await Repository.upsert_user_persona(d)


@router.post("/user-personas/{persona_id}/activate")
async def activate_user_persona(persona_id: str):
    success = await Repository.set_active_user_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"active_id": persona_id}


@router.delete("/user-personas/{persona_id}")
async def delete_user_persona(persona_id: str):
    success = await Repository.delete_user_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"deleted": True}


# --- Session Routes ---
@router.get("/characters/{char_id}/sessions", response_model=List[SessionRecord])
async def list_character_sessions(char_id: str):
    return await Repository.get_sessions_for_character(char_id)


@router.post("/characters/{char_id}/sessions", response_model=SessionRecord)
async def create_character_session(char_id: str, title: Optional[str] = "New Chat"):
    char = await Repository.get_character(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return await Repository.create_session(character_id=char_id, title=title or "New Chat")


@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str):
    session = await Repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await Repository.get_session_messages(session_id)
    facts = await Repository.get_session_facts(session_id)
    char = await Repository.get_character(session.character_id)
    return {
        "session": session,
        "character": char,
        "messages": messages,
        "facts": facts,
    }


@router.put("/sessions/{session_id}/title")
async def update_session_title(session_id: str, data: TitleUpdate):
    success = await Repository.update_session_title(session_id, data.title)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"updated": True, "title": data.title}


@router.put("/sessions/{session_id}/memory")
async def update_session_memory(session_id: str, data: MemoryUpdate):
    success = await Repository.update_session_memory_notes(session_id, data.memory_notes)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"updated": True, "memory_notes": data.memory_notes}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    success = await Repository.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "id": session_id}


# --- Message Routes ---
@router.put("/messages/{msg_id}", response_model=Dict[str, Any])
async def update_message(msg_id: str, data: MessageContentUpdate):
    success = await Repository.update_message_content(msg_id, data.content)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"updated": True, "content": data.content}


@router.post("/messages/{msg_id}/swipe", response_model=MessageRecord)
async def set_message_swipe(msg_id: str, data: SwipeSelect):
    record = await Repository.set_message_swipe(msg_id, data.swipe_index)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid swipe index or message not found")
    return record


@router.delete("/messages/{msg_id}")
async def delete_message(msg_id: str):
    success = await Repository.delete_message(msg_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"deleted": True, "id": msg_id}


@router.post("/sessions/{session_id}/messages", response_model=MessageRecord)
async def create_session_message(session_id: str, data: MessageCreate):
    session = await Repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await Repository.add_message(
        session_id=session_id,
        role=data.role,
        content=data.content,
        image_url=data.image_url or "",
    )


# --- Facts Routes ---
@router.get("/sessions/{session_id}/facts", response_model=List[MemoryFactRecord])
async def get_session_facts(session_id: str):
    return await Repository.get_session_facts(session_id)


@router.post("/sessions/{session_id}/facts", response_model=MemoryFactRecord)
async def add_session_fact(session_id: str, data: FactCreate):
    return await Repository.add_memory_fact(
        session_id=session_id,
        fact_text=data.fact_text,
        category=data.category,
    )


@router.delete("/facts/{fact_id}")
async def delete_fact(fact_id: str):
    success = await Repository.delete_memory_fact(fact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fact not found")
    return {"deleted": True}


# --- Models & Settings ---
@router.get("/models")
async def get_available_models():
    """Dynamically probes Ollama and LM Studio endpoints."""
    return await detect_all_runners()


@router.get("/settings")
async def get_settings():
    db_settings = await Repository.get_all_settings()
    return {
        "runner": db_settings.get("runner", settings.DEFAULT_RUNNER),
        "ollama_url": db_settings.get("ollama_url", settings.OLLAMA_BASE_URL),
        "lmstudio_url": db_settings.get("lmstudio_url", settings.LMSTUDIO_BASE_URL),
        "model": db_settings.get("model", settings.DEFAULT_MODEL),
        "temperature": float(db_settings.get("temperature", settings.DEFAULT_TEMPERATURE)),
        "top_p": float(db_settings.get("top_p", settings.DEFAULT_TOP_P)),
        "min_p": float(db_settings.get("min_p", settings.DEFAULT_MIN_P)),
        "repeat_penalty": float(db_settings.get("repeat_penalty", settings.DEFAULT_REPEAT_PENALTY)),
        "max_tokens": int(db_settings.get("max_tokens", settings.DEFAULT_MAX_TOKENS)),
    }


@router.post("/settings")
async def save_settings(data: Dict[str, Any]):
    for k, v in data.items():
        await Repository.set_setting(k, str(v))
    return {"saved": True}


# --- Image Generation Routes (SD WebUI Forge) ---
class ImageGenerateRequest(BaseModel):
    character_id: str
    session_id: str
    message_id: Optional[str] = None
    prompt_override: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None


@router.get("/image/status")
async def get_image_service_status():
    from src.image.client import ForgeClient
    client = ForgeClient()
    return await client.check_status()


@router.post("/image/launch")
async def launch_image_service():
    from src.image.launcher import launch_forge_background
    res = launch_forge_background()
    return res


@router.post("/image/generate")
async def generate_scene_image(data: ImageGenerateRequest):
    from src.image.client import ForgeClient

    char = await Repository.get_character(data.character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    # Build prompt
    prompt_parts = []
    if char.visual_tags:
        prompt_parts.append(char.visual_tags)

    if data.prompt_override and data.prompt_override.strip():
        prompt_parts.append(data.prompt_override.strip())
    elif data.message_id:
        # Extract scene context from the message content
        session_msgs = await Repository.get_session_messages(data.session_id)
        target = next((m for m in session_msgs if m.id == data.message_id), None)
        if target:
            # Clean dialogue quotes and extract physical actions/setting
            clean_content = target.content.replace('"', '').strip()
            prompt_parts.append(clean_content[:180])
    elif char.scenario:
        prompt_parts.append(char.scenario[:150])

    prompt_parts.append("masterpiece, best quality, highly detailed, photorealistic, 8k")
    final_prompt = ", ".join(prompt_parts)

    final_neg = char.negative_prompt.strip() or settings.DEFAULT_NEGATIVE_PROMPT

    w = data.width or settings.DEFAULT_IMAGE_WIDTH
    h = data.height or settings.DEFAULT_IMAGE_HEIGHT
    s = data.steps or settings.DEFAULT_IMAGE_STEPS
    cfg = data.cfg_scale or settings.DEFAULT_IMAGE_CFG

    client = ForgeClient()
    result = await client.generate_image(
        prompt=final_prompt,
        negative_prompt=final_neg,
        width=w,
        height=h,
        steps=s,
        cfg_scale=cfg,
    )

    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Image generation failed"))

    img_url = result.get("image_url", "")
    if data.message_id and img_url:
        await Repository.set_message_image(data.message_id, img_url)

    return {
        "success": True,
        "image_url": img_url,
        "message_id": data.message_id,
        "prompt": final_prompt,
    }

