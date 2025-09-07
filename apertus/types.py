from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

# Shared

class APIList(BaseModel):
    object: Literal["list"]

class ModelInfo(BaseModel):
    id: str
    object: Optional[str] = None
    created: Optional[int] = None
    owned_by: Optional[str] = None
    # Any additional fields as exposed by the provider
    raw: Dict[str, Any] = Field(default_factory=dict)

class ModelsList(APIList):
    data: List[ModelInfo]

# Chat types (OpenAI-like)

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None

class ChatChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class ChatChoiceMessage(BaseModel):
    role: str
    content: str

class ChatChoice(BaseModel):
    index: int
    message: Optional[ChatChoiceMessage] = None
    finish_reason: Optional[str] = None
    delta: Optional[ChatChoiceDelta] = None  # for streaming chunks

class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

class ChatCompletion(BaseModel):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: Optional[str] = None
    object: Optional[str] = None
    created: Optional[int] = None
    model: Optional[str] = None
    choices: List[ChatChoice]

class StreamEvent(BaseModel):
    """High-level streaming event wrapper.

    - delta: concatenated text delta for the first choice (common case)
    - raw: the raw chunk object from the provider
    """
    delta: Optional[str] = None
    choice_index: int = 0
    raw: ChatCompletionChunk

# Request schemas

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = None
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
