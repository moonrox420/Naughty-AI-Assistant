import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.config import settings
from src.db.repository import MessageRecord, Repository
from src.image.gpu_lock import gpu_lock
from src.llm.client import LLMClient
from src.llm.models import ChatMessage, GenerationParams
from src.memory.extractor import FactExtractor
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)
ws_router = APIRouter()

# Keep active cancellation events keyed by session_id
_active_cancellations: Dict[str, asyncio.Event] = {}


@ws_router.websocket("/ws/chat/{session_id}")
async def chat_websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    llm_client = LLMClient()
    cancel_event = asyncio.Event()
    _active_cancellations[session_id] = cancel_event

    try:
        while True:
            raw_text = await websocket.receive_text()
            if not raw_text:
                continue

            try:
                payload = json.loads(raw_text)
            except json.JSONDecodeError:
                await websocket.send_json({"event": "error", "message": "Invalid JSON format"})
                continue

            action = payload.get("action", "send")

            # Check if this is a stop command
            if action == "stop":
                cancel_event.set()
                await websocket.send_json({"event": "stopped", "session_id": session_id})
                continue

            # Reset cancel event for new generation
            cancel_event.clear()

            # Retrieve session details
            session = await Repository.get_session(session_id)
            if not session:
                await websocket.send_json({"event": "error", "message": "Session not found"})
                continue

            character = await Repository.get_character(session.character_id)
            if not character:
                await websocket.send_json({"event": "error", "message": "Character not found"})
                continue

            user_persona = (
                await Repository.get_active_user_persona()
                if not session.user_persona_id
                else await Repository.get_active_user_persona()
            )

            # Build generation parameters from client payload or defaults
            p = payload.get("params", {})
            params = GenerationParams(
                model=p.get("model") or settings.DEFAULT_MODEL,
                runner=p.get("runner") or settings.DEFAULT_RUNNER,
                temperature=float(p.get("temperature", settings.DEFAULT_TEMPERATURE)),
                top_p=float(p.get("top_p", settings.DEFAULT_TOP_P)),
                min_p=float(p.get("min_p", settings.DEFAULT_MIN_P)),
                repeat_penalty=float(p.get("repeat_penalty", settings.DEFAULT_REPEAT_PENALTY)),
                max_tokens=int(p.get("max_tokens", settings.DEFAULT_MAX_TOKENS)),
            )

            # Validate that a model is selected
            if not params.model:
                await websocket.send_json(
                    {
                        "event": "error",
                        "message": "No model selected. Please select or configure a model in Settings.",
                    }
                )
                continue

            # --- Action: SEND (New user message) ---
            if action == "send":
                user_text = payload.get("content", "").strip()
                if not user_text:
                    continue

                # 1. Save user message to database
                user_msg = await Repository.add_message(
                    session_id=session_id, role="user", content=user_text
                )
                await websocket.send_json({"event": "user_saved", "message": user_msg.model_dump()})

                # 2. Fetch updated history and build prompt context
                history = await Repository.get_session_messages(session_id)
                prompt_messages = await MemoryManager.build_prompt_context(
                    session=session,
                    character=character,
                    user_persona=user_persona,
                    history_messages=history,
                    max_sliding_turns=settings.CONTEXT_SLIDING_WINDOW_TURNS,
                )

                # 3. Stream assistant tokens
                accumulated_text = []
                await websocket.send_json({"event": "stream_start", "role": "assistant"})

                async with gpu_lock:
                    async for delta in llm_client.stream_chat(
                        messages=prompt_messages, params=params, cancel_event=cancel_event
                    ):
                        if delta.content:
                            accumulated_text.append(delta.content)
                            await websocket.send_json(
                                {
                                    "event": "stream_chunk",
                                    "delta": delta.content,
                                    "is_done": delta.is_done,
                                }
                            )
                        if delta.is_done:
                            break

                full_reply = "".join(accumulated_text).strip()

                # 4. Save assistant reply to database
                if full_reply:
                    assistant_msg = await Repository.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=full_reply,
                        alternatives=[full_reply],
                    )
                    await websocket.send_json(
                        {"event": "stream_done", "message": assistant_msg.model_dump()}
                    )

                    # 5. Non-blocking background fact extraction
                    recent_turns = await Repository.get_session_messages(session_id)
                    asyncio.create_task(
                        FactExtractor.extract_and_persist_facts_task(
                            session_id=session_id,
                            user_persona_id=user_persona.id if user_persona else None,
                            recent_messages=recent_turns,
                            model=params.model,
                            runner=params.runner,
                        )
                    )
                else:
                    await websocket.send_json(
                        {"event": "stream_done", "message": None, "cancelled": True}
                    )

            # --- Action: REGENERATE (Swipe alternative for assistant turn) ---
            elif action == "regenerate":
                target_msg_id = payload.get("message_id")
                history = await Repository.get_session_messages(session_id)

                # Find target turn index
                target_idx = -1
                for idx, m in enumerate(history):
                    if m.id == target_msg_id and m.role == "assistant":
                        target_idx = idx
                        break

                if target_idx == -1:
                    await websocket.send_json(
                        {"event": "error", "message": "Target message for regeneration not found"}
                    )
                    continue

                # Context is history up to just before this assistant turn
                sub_history = history[:target_idx]
                prompt_messages = await MemoryManager.build_prompt_context(
                    session=session,
                    character=character,
                    user_persona=user_persona,
                    history_messages=sub_history,
                )

                accumulated_text = []
                await websocket.send_json(
                    {
                        "event": "stream_start",
                        "role": "assistant",
                        "is_regenerate": True,
                        "target_id": target_msg_id,
                    }
                )

                async with gpu_lock:
                    async for delta in llm_client.stream_chat(
                        messages=prompt_messages, params=params, cancel_event=cancel_event
                    ):
                        if delta.content:
                            accumulated_text.append(delta.content)
                            await websocket.send_json(
                                {
                                    "event": "stream_chunk",
                                    "delta": delta.content,
                                    "is_done": delta.is_done,
                                }
                            )
                        if delta.is_done:
                            break

                new_reply = "".join(accumulated_text).strip()
                if new_reply:
                    updated_record = await Repository.append_message_alternative(
                        target_msg_id, new_reply
                    )
                    if updated_record:
                        await websocket.send_json(
                            {"event": "stream_done", "message": updated_record.model_dump()}
                        )

            # --- Action: CONTINUE (Continue generating assistant text) ---
            elif action == "continue":
                target_msg_id = payload.get("message_id")
                history = await Repository.get_session_messages(session_id)
                target_msg: Optional[MessageRecord] = None
                for m in history:
                    if m.id == target_msg_id and m.role == "assistant":
                        target_msg = m
                        break

                if not target_msg:
                    await websocket.send_json(
                        {"event": "error", "message": "Target message not found"}
                    )
                    continue

                prompt_messages = await MemoryManager.build_prompt_context(
                    session=session,
                    character=character,
                    user_persona=user_persona,
                    history_messages=history,
                )
                prompt_messages.append(
                    ChatMessage(
                        role="system",
                        content="Continue writing the assistant's previous message seamlessly without repeating any previous words.",
                    )
                )

                accumulated_text = []
                await websocket.send_json(
                    {
                        "event": "stream_start",
                        "role": "assistant",
                        "is_continue": True,
                        "target_id": target_msg_id,
                    }
                )

                async with gpu_lock:
                    async for delta in llm_client.stream_chat(
                        messages=prompt_messages, params=params, cancel_event=cancel_event
                    ):
                        if delta.content:
                            accumulated_text.append(delta.content)
                            await websocket.send_json(
                                {
                                    "event": "stream_chunk",
                                    "delta": delta.content,
                                    "is_done": delta.is_done,
                                }
                            )
                        if delta.is_done:
                            break

                continuation = "".join(accumulated_text)
                if continuation:
                    merged = (target_msg.content + " " + continuation).strip()
                    await Repository.update_message_content(target_msg.id, merged)
                    updated = await Repository.get_session_messages(session_id)
                    latest_target = next((m for m in updated if m.id == target_msg.id), None)
                    if latest_target:
                        await websocket.send_json(
                            {"event": "stream_done", "message": latest_target.model_dump()}
                        )

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session {session_id}")
    except Exception as ex:
        logger.error(f"WebSocket error in session {session_id}: {ex}")
    finally:
        _active_cancellations.pop(session_id, None)
