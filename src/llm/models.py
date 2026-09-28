from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str
    name: str
    runner: str  # "ollama" | "lmstudio" | "custom"
    size: Optional[str] = None
    modified_at: Optional[str] = None
    family: Optional[str] = None


class GenerationParams(BaseModel):
    model: str
    runner: str = "ollama"  # "ollama" | "lmstudio" | "custom"
    temperature: float = 0.85
    top_p: float = 0.90
    min_p: float = 0.05
    repeat_penalty: float = 1.15
    max_tokens: int = 2048
    stop_sequences: List[str] = Field(default_factory=lambda: ["<|endoftext|>", "### Instruction:", "User:"])


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class StreamDelta(BaseModel):
    content: str
    is_done: bool = False
    finish_reason: Optional[str] = None
