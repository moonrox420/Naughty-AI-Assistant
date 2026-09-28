import asyncio
import json
from typing import AsyncGenerator, List, Optional
import httpx

from src.config import settings
from src.llm.models import ChatMessage, GenerationParams, StreamDelta


class LLMClient:
    def __init__(self) -> None:
        self.http_timeout = httpx.Timeout(120.0, connect=10.0)

    def _resolve_base_url(self, runner: str) -> str:
        if runner == "lmstudio":
            return settings.LMSTUDIO_BASE_URL.rstrip("/")
        if runner == "custom" and settings.CUSTOM_BASE_URL:
            return settings.CUSTOM_BASE_URL.rstrip("/")
        return settings.OLLAMA_BASE_URL.rstrip("/")

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        params: GenerationParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[StreamDelta, None]:
        base_url = self._resolve_base_url(params.runner)

        if params.runner == "ollama":
            async for delta in self._stream_ollama(base_url, messages, params, cancel_event):
                yield delta
        else:
            # LM Studio or OpenAI-compatible endpoint
            async for delta in self._stream_openai_compatible(base_url, messages, params, cancel_event):
                yield delta

    async def _stream_ollama(
        self,
        base_url: str,
        messages: List[ChatMessage],
        params: GenerationParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[StreamDelta, None]:
        url = f"{base_url}/api/chat"
        payload = {
            "model": params.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "temperature": params.temperature,
                "top_p": params.top_p,
                "min_p": params.min_p,
                "repeat_penalty": params.repeat_penalty,
                "num_predict": params.max_tokens,
                "stop": params.stop_sequences,
            },
        }

        async with httpx.AsyncClient(timeout=self.http_timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        yield StreamDelta(
                            content=f"\n[Error from Ollama ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}]",
                            is_done=True,
                            finish_reason="error",
                        )
                        return

                    async for line in response.aiter_lines():
                        if cancel_event and cancel_event.is_set():
                            yield StreamDelta(content="", is_done=True, finish_reason="cancelled")
                            return

                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            msg = data.get("message", {})
                            content = msg.get("content", "")
                            done = data.get("done", False)

                            if content:
                                yield StreamDelta(content=content, is_done=False)

                            if done:
                                yield StreamDelta(content="", is_done=True, finish_reason="stop")
                                return
                        except json.JSONDecodeError:
                            continue
            except httpx.ConnectError:
                yield StreamDelta(
                    content="\n[Error: Could not connect to Ollama. Please make sure Ollama is running at "
                    + base_url
                    + " (run 'ollama serve')]",
                    is_done=True,
                    finish_reason="connection_error",
                )
            except Exception as ex:
                yield StreamDelta(
                    content=f"\n[Generation error: {str(ex)}]",
                    is_done=True,
                    finish_reason="error",
                )

    async def _stream_openai_compatible(
        self,
        base_url: str,
        messages: List[ChatMessage],
        params: GenerationParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[StreamDelta, None]:
        url = f"{base_url}/chat/completions"
        payload = {
            "model": params.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "temperature": params.temperature,
            "top_p": params.top_p,
            "max_tokens": params.max_tokens,
            "presence_penalty": (params.repeat_penalty - 1.0) if params.repeat_penalty > 1.0 else 0.0,
            "stop": params.stop_sequences,
        }

        headers = {}
        if settings.CUSTOM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.CUSTOM_API_KEY}"

        async with httpx.AsyncClient(timeout=self.http_timeout) as client:
            try:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        yield StreamDelta(
                            content=f"\n[Error from LM Studio/Inference server ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}]",
                            is_done=True,
                            finish_reason="error",
                        )
                        return

                    async for line in response.aiter_lines():
                        if cancel_event and cancel_event.is_set():
                            yield StreamDelta(content="", is_done=True, finish_reason="cancelled")
                            return

                        line_str = line.strip()
                        if not line_str or not line_str.startswith("data:"):
                            continue

                        raw_data = line_str[5:].strip()
                        if raw_data == "[DONE]":
                            yield StreamDelta(content="", is_done=True, finish_reason="stop")
                            return

                        try:
                            data = json.loads(raw_data)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                finish_reason = choices[0].get("finish_reason")
                                text_piece = delta.get("content", "")
                                if text_piece:
                                    yield StreamDelta(content=text_piece, is_done=False)
                                if finish_reason in ["stop", "length"]:
                                    yield StreamDelta(content="", is_done=True, finish_reason=finish_reason)
                                    return
                        except json.JSONDecodeError:
                            continue
            except httpx.ConnectError:
                yield StreamDelta(
                    content="\n[Error: Could not connect to inference runner at "
                    + base_url
                    + ". Check if LM Studio local server is started]",
                    is_done=True,
                    finish_reason="connection_error",
                )
            except Exception as ex:
                yield StreamDelta(
                    content=f"\n[Inference error: {str(ex)}]",
                    is_done=True,
                    finish_reason="error",
                )

    async def generate_text(
        self,
        messages: List[ChatMessage],
        model: str,
        runner: str = "ollama",
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> str:
        """Non-streaming generation helper for background tasks."""
        params = GenerationParams(
            model=model,
            runner=runner,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        full_text = []
        async for chunk in self.stream_chat(messages, params):
            if chunk.content:
                full_text.append(chunk.content)
        return "".join(full_text).strip()
