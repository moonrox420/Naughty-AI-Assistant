from typing import List, Optional
from src.config import settings
from src.db.repository import (
    CharacterRecord,
    MemoryFactRecord,
    MessageRecord,
    Repository,
    SessionRecord,
    UserPersonaRecord,
)
from src.llm.models import ChatMessage


class MemoryManager:
    @staticmethod
    async def build_prompt_context(
        session: SessionRecord,
        character: CharacterRecord,
        user_persona: Optional[UserPersonaRecord],
        history_messages: List[MessageRecord],
        max_sliding_turns: int = settings.CONTEXT_SLIDING_WINDOW_TURNS,
    ) -> List[ChatMessage]:
        """
        Assembles full contextual prompt combining:
        1. Character Definition & System Instructions
        2. User Persona Details
        3. Active Session Memory Scratchpad & Extracted Facts
        4. Example Dialogue
        5. Sliding Window of Recent History
        """
        user_name = user_persona.name if user_persona else "User"
        char_name = character.name

        # 1. System Prompt & Character Persona
        system_blocks = []

        base_system = character.system_prompt.strip()
        if not base_system:
            base_system = f"You are {char_name}. Stay in character at all times. Engage in immersive, expressive roleplay with {user_name}."
        system_blocks.append(base_system)

        if character.description:
            system_blocks.append(f"### Character Description:\n{character.description}")
        if character.personality:
            system_blocks.append(f"### Character Personality & Traits:\n{character.personality}")
        if character.scenario:
            system_blocks.append(f"### Current Scenario / Setting:\n{character.scenario}")

        # 2. User Persona
        if user_persona:
            user_block = [f"### User Info ({user_name}):"]
            if user_persona.pronouns:
                user_block.append(f"- Pronouns: {user_persona.pronouns}")
            if user_persona.traits:
                user_block.append(f"- Traits / Demeanor: {user_persona.traits}")
            if user_persona.description:
                user_block.append(f"- Background / Bio: {user_persona.description}")
            system_blocks.append("\n".join(user_block))

        # 3. Persistent Memory Scratchpad & Extracted Facts
        mem_blocks = []
        if session.memory_notes and session.memory_notes.strip():
            mem_blocks.append(f"Session Notes:\n{session.memory_notes.strip()}")

        facts: List[MemoryFactRecord] = await Repository.get_session_facts(session.id)
        if facts:
            fact_lines = [f"- {f.fact_text} (Category: {f.category})" for f in facts[:10]]
            mem_blocks.append("Retained Long-Term Facts:\n" + "\n".join(fact_lines))

        if mem_blocks:
            system_blocks.append("### Important Context & Memories:\n" + "\n\n".join(mem_blocks))

        # Formatting guidelines
        system_blocks.append(
            "### Roleplay Directives:\n"
            "- Wrap all physical actions, body language, facial expressions, and sensory descriptions in asterisks (*like this*).\n"
            "- Put all spoken dialogue inside double quotation marks (\"like this\").\n"
            "- Maintain continuous immersion and never break character."
        )

        full_system_text = "\n\n".join(system_blocks)
        prompt_messages: List[ChatMessage] = [
            ChatMessage(role="system", content=full_system_text)
        ]

        # 4. Example Dialogue (if present)
        if character.example_dialogue and character.example_dialogue.strip():
            # Replace placeholder variables {{char}} and {{user}}
            ex_text = (
                character.example_dialogue.replace("{{char}}", char_name)
                .replace("{{user}}", user_name)
                .replace("<START>", "")
                .strip()
            )
            if ex_text:
                prompt_messages.append(
                    ChatMessage(
                        role="system",
                        content=f"### Example Dialogue Style for {char_name}:\n{ex_text}",
                    )
                )

        # 5. Sliding Window of Conversation Messages
        # Filter out system turns from history, taking up to max_sliding_turns
        valid_history = [
            m for m in history_messages if m.role in ["user", "assistant"] and m.content.strip()
        ]
        windowed = valid_history[-max_sliding_turns:]

        for msg in windowed:
            prompt_messages.append(ChatMessage(role=msg.role, content=msg.content))

        return prompt_messages
