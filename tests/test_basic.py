import os
import pytest

from apertus import Apertus

API_KEY = os.getenv("APERTUS_API_KEY", "test-key")


def test_client_init():
    client = Apertus(api_key=API_KEY)
    assert client.models is not None
    assert client.chat is not None


def test_models_list_builds_request(monkeypatch):
    client = Apertus(api_key=API_KEY)

    called = {}

    class FakeHTTP:
        def get(self, path):
            called["path"] = path
            return {"object": "list", "data": []}

    client._http = FakeHTTP()  # type: ignore
    client.models._http = client._http  # type: ignore

    models = client.models.list()
    assert called["path"] == "/v1/models"
    assert models.object == "list"


def test_chat_create_builds_request(monkeypatch):
    client = Apertus(api_key=API_KEY)

    called = {}

    class FakeHTTP:
        def post_json(self, path, json):
            called["path"] = path
            called["json"] = json
            return {
                "id": "abc",
                "object": "chat.completion",
                "created": 0,
                "model": "test",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }

    client._http = FakeHTTP()  # type: ignore
    client.chat.completions._http = client._http  # type: ignore

    resp = client.chat.completions.create(
        model="test",
        messages=[{"role": "user", "content": "hello"}],
    )
    assert called["path"] == "/v1/chat/completions"
    assert "model" in called["json"]
    assert resp.object == "chat.completion"


def test_stream_parsing(monkeypatch):
    client = Apertus(api_key=API_KEY)

    chunks = [
        b"data: {\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\"}}]}\n",
        b"data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\"he\"}}]}\n",
        b"data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\"llo\"}}]}\n",
        b"data: [DONE]\n",
    ]

    class FakeHTTP:
        def post_stream(self, path, json):
            for c in chunks:
                yield c

    client._http = FakeHTTP()  # type: ignore
    client.chat.completions._http = client._http  # type: ignore

    result = []
    for ev in client.chat.completions.stream(model="x", messages=[{"role": "user", "content": "hi"}]):
        if ev.delta:
            result.append(ev.delta)

    assert "".join(result) == "hello"
