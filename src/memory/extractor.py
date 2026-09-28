import asyncio
import json
import logging
from typing import List, Optional
from src.config import settings
from src.db.repository import MessageRecord, Repository
from src.llm.client import LLMClient
from src.llm.models import ChatMessage

logger = logging.getLogger(__name__)


class FactExtractor:
    @staticmethod
    async def extract_and_persist_facts_task(
        session_id: str,
        user_persona_id: Optional[str],
        recent_messages: List[MessageRecord],
        model: str,
        runner: str = "ollama",
    ) -> None:
        """
        Background worker that inspects recent turns to extract persistent facts
        about the user or relationship.
        """
        if not settings.ENABLE_FACT_EXTRACTION or not model:
            return

        # Need at least 2 messages (one user, one assistant)
        if len(recent_messages) < 2:
            return

        extract_model = settings.FACT_EXTRACTION_MODEL or model
        conversation_snippet = []
        for m in recent_messages[-4:]:
            conversation_snippet.append(f"{m.role.upper()}: {m.content}")

        dialogue_text = "\n".join(conversation_snippet)

        prompt = (
            "You are a precise memory extraction engine for a conversational companion.\n"
            "Analyze the conversation turns below. Identify any NEW, ENDURING, or SPECIFIC facts, preferences, secrets, "
            "or relationship milestones revealed about the USER.\n\n"
            "Rules:\n"
            "1. Ignore momentary remarks, greetings, or questions.\n"
            "2. Only extract enduring facts (e.g. 'User loves dark roast coffee', 'User works as an aerospace engineer', 'User dislikes being interrupted').\n"
            "3. If nothing new or meaningful is revealed, return an empty array: []\n"
            "4. Respond strictly with a JSON array of objects: [{\"fact\": \"...\", \"category\": \"preference|secret|milestone|general\"}]\n\n"
            f"Conversation:\n{dialogue_text}\n\nJSON Output:"
        )

        messages = [
            ChatMessage(role="system", content="You are a JSON-only extractor. Output only valid JSON."),
            ChatMessage(role="user", content=prompt),
        ]

        from src.image.gpu_lock import gpu_lock
        llm = LLMClient()
        try:
            async with gpu_lock:
                raw_response = await asyncio.wait_for(
                    llm.generate_text(
                        messages=messages,
                        model=extract_model,
                        runner=runner,
                        temperature=0.1,
                        max_tokens=256,
                    ),
                    timeout=25.0,
                )

            # Clean JSON response of markdown code blocks
            clean_text = raw_response.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            if not clean_text or clean_text == "[]":
                return

            parsed = json.loads(clean_text)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "fact" in item:
                        fact_str = str(item["fact"]).strip()
                        category = str(item.get("category", "general")).strip()
                        if fact_str and len(fact_str) > 3:
                            await Repository.add_memory_fact(
                                session_id=session_id,
                                fact_text=fact_str,
                                category=category,
                                user_persona_id=user_persona_id,
                            )
        except asyncio.TimeoutError:
            logger.debug("Fact extraction timed out, continuing without blocking.")
        except Exception as ex:
            logger.debug(f"Fact extraction skipped or parse error: {ex}")
