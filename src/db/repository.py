import json
import uuid
from typing import Any, Dict, List, Optional
import aiosqlite
from pydantic import BaseModel, Field

from src.db.database import get_db_connection


class CharacterRecord(BaseModel):
    id: str
    name: str
    tagline: str = ""
    avatar: str = ""
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_message: str = ""
    example_dialogue: str = ""
    system_prompt: str = ""
    visual_tags: str = ""
    negative_prompt: str = ""
    is_builtin: int = 0
    created_at: str = ""
    updated_at: str = ""


class UserPersonaRecord(BaseModel):
    id: str
    name: str
    pronouns: str = ""
    description: str = ""
    traits: str = ""
    is_active: int = 0
    created_at: str = ""
    updated_at: str = ""


class SessionRecord(BaseModel):
    id: str
    character_id: str
    user_persona_id: Optional[str] = None
    title: str
    memory_notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class MessageRecord(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    swipe_index: int = 0
    alternatives: List[str] = Field(default_factory=list)
    image_url: str = ""
    created_at: str = ""


class MemoryFactRecord(BaseModel):
    id: str
    session_id: str
    user_persona_id: Optional[str] = None
    fact_text: str
    category: str = "general"
    confidence: float = 1.0
    is_active: int = 1
    created_at: str = ""


class Repository:
    # --- Characters ---
    @staticmethod
    async def get_characters() -> List[CharacterRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM characters ORDER BY is_builtin DESC, updated_at DESC"
            )
            rows = await cursor.fetchall()
            return [CharacterRecord(**dict(row)) for row in rows]

    @staticmethod
    async def get_character(character_id: str) -> Optional[CharacterRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM characters WHERE id = ?", (character_id,)
            )
            row = await cursor.fetchone()
            return CharacterRecord(**dict(row)) if row else None

    @staticmethod
    async def upsert_character(char: Dict[str, Any]) -> CharacterRecord:
        char_id = char.get("id") or str(uuid.uuid4())
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO characters (
                    id, name, tagline, avatar, description, personality,
                    scenario, first_message, example_dialogue, system_prompt, visual_tags, negative_prompt, is_builtin, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    tagline = excluded.tagline,
                    avatar = excluded.avatar,
                    description = excluded.description,
                    personality = excluded.personality,
                    scenario = excluded.scenario,
                    first_message = excluded.first_message,
                    example_dialogue = excluded.example_dialogue,
                    system_prompt = excluded.system_prompt,
                    visual_tags = excluded.visual_tags,
                    negative_prompt = excluded.negative_prompt,
                    is_builtin = excluded.is_builtin,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    char_id,
                    char["name"],
                    char.get("tagline", ""),
                    char.get("avatar", ""),
                    char.get("description", ""),
                    char.get("personality", ""),
                    char.get("scenario", ""),
                    char.get("first_message", ""),
                    char.get("example_dialogue", ""),
                    char.get("system_prompt", ""),
                    char.get("visual_tags", ""),
                    char.get("negative_prompt", ""),
                    char.get("is_builtin", 0),
                ),
            )
            await db.commit()
            res = await Repository.get_character(char_id)
            if not res:
                raise RuntimeError(f"Failed to retrieve character {char_id} after upsert")
            return res

    @staticmethod
    async def delete_character(character_id: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "DELETE FROM characters WHERE id = ?", (character_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    # --- User Personas ---
    @staticmethod
    async def get_user_personas() -> List[UserPersonaRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM user_personas ORDER BY is_active DESC, updated_at DESC"
            )
            rows = await cursor.fetchall()
            return [UserPersonaRecord(**dict(row)) for row in rows]

    @staticmethod
    async def get_active_user_persona() -> Optional[UserPersonaRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM user_personas WHERE is_active = 1 LIMIT 1"
            )
            row = await cursor.fetchone()
            if row:
                return UserPersonaRecord(**dict(row))
            # Fallback to first available persona
            cursor = await db.execute(
                "SELECT * FROM user_personas ORDER BY created_at ASC LIMIT 1"
            )
            fallback = await cursor.fetchone()
            return UserPersonaRecord(**dict(fallback)) if fallback else None

    @staticmethod
    async def upsert_user_persona(persona: Dict[str, Any]) -> UserPersonaRecord:
        persona_id = persona.get("id") or str(uuid.uuid4())
        is_active = persona.get("is_active", 0)
        async with get_db_connection() as db:
            if is_active == 1:
                await db.execute("UPDATE user_personas SET is_active = 0")
            await db.execute(
                """
                INSERT INTO user_personas (
                    id, name, pronouns, description, traits, is_active, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    pronouns = excluded.pronouns,
                    description = excluded.description,
                    traits = excluded.traits,
                    is_active = excluded.is_active,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    persona_id,
                    persona["name"],
                    persona.get("pronouns", ""),
                    persona.get("description", ""),
                    persona.get("traits", ""),
                    is_active,
                ),
            )
            await db.commit()
            cursor = await db.execute(
                "SELECT * FROM user_personas WHERE id = ?", (persona_id,)
            )
            row = await cursor.fetchone()
            return UserPersonaRecord(**dict(row))

    @staticmethod
    async def set_active_user_persona(persona_id: str) -> bool:
        async with get_db_connection() as db:
            await db.execute("UPDATE user_personas SET is_active = 0")
            cursor = await db.execute(
                "UPDATE user_personas SET is_active = 1 WHERE id = ?", (persona_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    @staticmethod
    async def delete_user_persona(persona_id: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "DELETE FROM user_personas WHERE id = ?", (persona_id,)
            )
            await db.commit()
            # If active was deleted, make sure at least one is active
            active = await Repository.get_active_user_persona()
            if not active:
                first = await db.execute("SELECT id FROM user_personas LIMIT 1")
                row = await first.fetchone()
                if row:
                    await db.execute(
                        "UPDATE user_personas SET is_active = 1 WHERE id = ?", (row[0],)
                    )
                    await db.commit()
            return cursor.rowcount > 0

    # --- Sessions ---
    @staticmethod
    async def get_sessions_for_character(character_id: str) -> List[SessionRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE character_id = ? ORDER BY updated_at DESC",
                (character_id,),
            )
            rows = await cursor.fetchall()
            return [SessionRecord(**dict(row)) for row in rows]

    @staticmethod
    async def get_session(session_id: str) -> Optional[SessionRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            )
            row = await cursor.fetchone()
            return SessionRecord(**dict(row)) if row else None

    @staticmethod
    async def create_session(
        character_id: str,
        title: str = "New Chat",
        user_persona_id: Optional[str] = None,
    ) -> SessionRecord:
        session_id = str(uuid.uuid4())
        if not user_persona_id:
            active_p = await Repository.get_active_user_persona()
            if active_p:
                user_persona_id = active_p.id

        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO sessions (id, character_id, user_persona_id, title)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, character_id, user_persona_id, title),
            )
            await db.commit()

        # Seed character's first_message as initial assistant turn if present
        char = await Repository.get_character(character_id)
        if char and char.first_message.strip():
            await Repository.add_message(
                session_id=session_id,
                role="assistant",
                content=char.first_message.strip(),
            )

        res = await Repository.get_session(session_id)
        if not res:
            raise RuntimeError(f"Failed to retrieve session {session_id} after create")
        return res

    @staticmethod
    async def update_session_title(session_id: str, title: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, session_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    @staticmethod
    async def update_session_memory_notes(session_id: str, notes: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "UPDATE sessions SET memory_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (notes, session_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "DELETE FROM sessions WHERE id = ?", (session_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    # --- Messages ---
    @staticmethod
    async def get_session_messages(session_id: str) -> List[MessageRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                try:
                    item["alternatives"] = json.loads(item.get("alternatives") or "[]")
                except Exception:
                    item["alternatives"] = [item["content"]]
                if not item["alternatives"] and item["content"]:
                    item["alternatives"] = [item["content"]]
                results.append(MessageRecord(**item))
            return results

    @staticmethod
    async def add_message(
        session_id: str,
        role: str,
        content: str,
        alternatives: Optional[List[str]] = None,
        image_url: str = "",
    ) -> MessageRecord:
        msg_id = str(uuid.uuid4())
        alts = alternatives if alternatives is not None else [content]
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO messages (id, session_id, role, content, swipe_index, alternatives, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (msg_id, session_id, role, content, 0, json.dumps(alts), image_url),
            )
            await db.execute(
                "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,),
            )
            await db.commit()
            cursor = await db.execute(
                "SELECT * FROM messages WHERE id = ?", (msg_id,)
            )
            row = await cursor.fetchone()
            item = dict(row)
            item["alternatives"] = json.loads(item["alternatives"])
            return MessageRecord(**item)

    @staticmethod
    async def set_message_image(message_id: str, image_url: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "UPDATE messages SET image_url = ? WHERE id = ?",
                (image_url, message_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    @staticmethod
    async def update_message_content(message_id: str, new_content: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM messages WHERE id = ?", (message_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return False
            item = dict(row)
            try:
                alts = json.loads(item.get("alternatives") or "[]")
            except Exception:
                alts = []
            idx = item.get("swipe_index", 0)
            if 0 <= idx < len(alts):
                alts[idx] = new_content
            else:
                alts = [new_content]

            await db.execute(
                """
                UPDATE messages
                SET content = ?, alternatives = ?
                WHERE id = ?
                """,
                (new_content, json.dumps(alts), message_id),
            )
            await db.commit()
            return True

    @staticmethod
    async def set_message_swipe(message_id: str, swipe_index: int) -> Optional[MessageRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM messages WHERE id = ?", (message_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            alts = json.loads(item.get("alternatives") or "[]")
            if not (0 <= swipe_index < len(alts)):
                return None
            new_content = alts[swipe_index]
            await db.execute(
                """
                UPDATE messages
                SET content = ?, swipe_index = ?
                WHERE id = ?
                """,
                (new_content, swipe_index, message_id),
            )
            await db.commit()
            item["content"] = new_content
            item["swipe_index"] = swipe_index
            item["alternatives"] = alts
            return MessageRecord(**item)

    @staticmethod
    async def append_message_alternative(
        message_id: str, new_alternative: str
    ) -> Optional[MessageRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM messages WHERE id = ?", (message_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            alts = json.loads(item.get("alternatives") or "[]")
            alts.append(new_alternative)
            new_idx = len(alts) - 1
            await db.execute(
                """
                UPDATE messages
                SET content = ?, swipe_index = ?, alternatives = ?
                WHERE id = ?
                """,
                (new_alternative, new_idx, json.dumps(alts), message_id),
            )
            await db.commit()
            item["content"] = new_alternative
            item["swipe_index"] = new_idx
            item["alternatives"] = alts
            return MessageRecord(**item)

    @staticmethod
    async def delete_message(message_id: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "DELETE FROM messages WHERE id = ?", (message_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    # --- Memory Facts ---
    @staticmethod
    async def get_session_facts(session_id: str) -> List[MemoryFactRecord]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM memory_facts WHERE session_id = ? AND is_active = 1 ORDER BY created_at DESC",
                (session_id,),
            )
            rows = await cursor.fetchall()
            return [MemoryFactRecord(**dict(row)) for row in rows]

    @staticmethod
    async def add_memory_fact(
        session_id: str,
        fact_text: str,
        category: str = "general",
        confidence: float = 1.0,
        user_persona_id: Optional[str] = None,
    ) -> MemoryFactRecord:
        fact_id = str(uuid.uuid4())
        async with get_db_connection() as db:
            # Check for duplicate facts in the same session
            existing = await db.execute(
                "SELECT id FROM memory_facts WHERE session_id = ? AND fact_text = ?",
                (session_id, fact_text),
            )
            row = await existing.fetchone()
            if row:
                cursor = await db.execute(
                    "SELECT * FROM memory_facts WHERE id = ?", (row[0],)
                )
                existing_row = await cursor.fetchone()
                return MemoryFactRecord(**dict(existing_row))

            await db.execute(
                """
                INSERT INTO memory_facts (id, session_id, user_persona_id, fact_text, category, confidence, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (fact_id, session_id, user_persona_id, fact_text, category, confidence),
            )
            await db.commit()
            cursor = await db.execute(
                "SELECT * FROM memory_facts WHERE id = ?", (fact_id,)
            )
            row = await cursor.fetchone()
            return MemoryFactRecord(**dict(row))

    @staticmethod
    async def delete_memory_fact(fact_id: str) -> bool:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "DELETE FROM memory_facts WHERE id = ?", (fact_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    # --- App Settings ---
    @staticmethod
    async def get_all_settings() -> Dict[str, str]:
        async with get_db_connection() as db:
            cursor = await db.execute("SELECT key, value FROM app_settings")
            rows = await cursor.fetchall()
            return {row["key"]: row["value"] for row in rows}

    @staticmethod
    async def set_setting(key: str, value: str) -> None:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )
            await db.commit()
