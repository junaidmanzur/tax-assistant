from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field

DEFAULT_THREAD = "default-thread"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(...)
    content: str = Field(...)

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    thread_id: Optional[str] = Field(default=DEFAULT_THREAD)
    # Optional: pass extra config if you want
    config: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    output: str
    messages: List[Dict[str, Any]]