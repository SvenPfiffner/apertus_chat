from __future__ import annotations
from typing import Any, AsyncGenerator, Dict, Generator, Iterable, List, Optional
import json

from .http import SyncHTTP, AsyncHTTP
from .types import (
    ModelsList,
    ModelInfo,
    ChatCompletion,
    ChatCompletionRequest,
    ChatCompletionChunk,
    StreamEvent,
)

MODELS_PATH = "/v1/models"
CHAT_COMPLETIONS_PATH = "/v1/chat/completions"

# Convenience sub-clients mirroring OpenAI structure

class _Models:
    def __init__(self, http: SyncHTTP):
        self._http = http

    def list(self) -> ModelsList:
        data = self._http.get(MODELS_PATH)
        # Accept both OpenAI-format and generic list
        return ModelsList.model_validate(data)

class _AsyncModels:
    def __init__(self, http: AsyncHTTP):
        self._http = http

    async def list(self) -> ModelsList:
        data = await self._http.get(MODELS_PATH)
        return ModelsList.model_validate(data)

class _ChatCompletions:
    def __init__(self, http: SyncHTTP):
        self._http = http

    def create(self, **kwargs) -> ChatCompletion:
        payload = ChatCompletionRequest(**kwargs).model_dump(exclude_none=True)
        data = self._http.post_json(CHAT_COMPLETIONS_PATH, json=payload)
        return ChatCompletion.model_validate(data)

    def stream(self, **kwargs) -> Generator[StreamEvent, None, None]:
        # Ensure stream flag is set
        payload = ChatCompletionRequest(**{**kwargs, "stream": True}).model_dump(exclude_none=True)
        for line in self._http.post_stream(CHAT_COMPLETIONS_PATH, json=payload):
            # Expect SSE-like lines: possibly starting with 'data: {...}'
            text = line.decode("utf-8") if isinstance(line, (bytes, bytearray)) else line
            text = text.strip()
            if not text:
                continue
            if text.startswith("data:"):
                text = text[len("data:"):].strip()
            if text == "[DONE]":
                break
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                continue
            chunk = ChatCompletionChunk.model_validate(obj)
            delta = None
            if chunk.choices:
                ch0 = chunk.choices[0]
                if ch0.delta and ch0.delta.content is not None:
                    delta = ch0.delta.content
            yield StreamEvent(delta=delta, choice_index=0, raw=chunk)

class _AsyncChatCompletions:
    def __init__(self, http: AsyncHTTP):
        self._http = http

    async def create(self, **kwargs) -> ChatCompletion:
        payload = ChatCompletionRequest(**kwargs).model_dump(exclude_none=True)
        data = await self._http.post_json(CHAT_COMPLETIONS_PATH, json=payload)
        return ChatCompletion.model_validate(data)

    async def stream(self, **kwargs) -> AsyncGenerator[StreamEvent, None]:
        payload = ChatCompletionRequest(**{**kwargs, "stream": True}).model_dump(exclude_none=True)
        async for line in self._http.post_stream(CHAT_COMPLETIONS_PATH, json=payload):
            text = line
            text = text.decode("utf-8") if isinstance(text, (bytes, bytearray)) else text
            text = text.strip()
            if not text:
                continue
            if text.startswith("data:"):
                text = text[len("data:"):].strip()
            if text == "[DONE]":
                break
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                continue
            chunk = ChatCompletionChunk.model_validate(obj)
            delta = None
            if chunk.choices:
                ch0 = chunk.choices[0]
                if ch0.delta and ch0.delta.content is not None:
                    delta = ch0.delta.content
            yield StreamEvent(delta=delta, choice_index=0, raw=chunk)

class _Chat:
    def __init__(self, http: SyncHTTP):
        self.completions = _ChatCompletions(http)

class _AsyncChat:
    def __init__(self, http: AsyncHTTP):
        self.completions = _AsyncChatCompletions(http)

class Apertus:
    def __init__(self, api_key: Optional[str] = None, *, base_url: str = None, timeout: float = 30.0):
        self._http = SyncHTTP(api_key=api_key, base_url=base_url or "https://api.publicai.co", timeout=timeout)
        self.models = _Models(self._http)
        self.chat = _Chat(self._http)

class AsyncApertus:
    def __init__(self, api_key: Optional[str] = None, *, base_url: str = None, timeout: float = 30.0):
        self._http = AsyncHTTP(api_key=api_key, base_url=base_url or "https://api.publicai.co", timeout=timeout)
        self.models = _AsyncModels(self._http)
        self.chat = _AsyncChat(self._http)
