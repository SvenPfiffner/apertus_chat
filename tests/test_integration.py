import os
import time
import pytest

from apertus import Apertus, ApertusAPIError

VALID_KEY = os.getenv("APERTUS_API_KEY")


def require_key():
    if not VALID_KEY:
        pytest.skip("APERTUS_API_KEY not set; skipping live integration tests")


def test_live_models_list_success():
    require_key()
    client = Apertus(api_key=VALID_KEY)
    models = client.models.list()
    assert models.object == "list"
    assert isinstance(models.data, list)
    # Capture at least one model id for follow-on tests
    ids = [m.id for m in models.data if getattr(m, "id", None)]
    assert len(ids) > 0


def pick_first_model_id(client: Apertus) -> str:
    models = client.models.list()
    ids = [m.id for m in models.data if getattr(m, "id", None)]
    assert ids, "No models available for this key"
    return ids[0]


def test_live_chat_completion_success():
    require_key()
    client = Apertus(api_key=VALID_KEY)
    model_id = pick_first_model_id(client)
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": "Reply with the word: pong"}],
        temperature=0,
        max_tokens=8,
    )
    assert resp.object == "chat.completion"
    assert resp.choices and resp.choices[0].message is not None
    assert isinstance(resp.choices[0].message.content, str)


def test_live_streaming_success_collects_tokens():
    require_key()
    client = Apertus(api_key=VALID_KEY)
    model_id = pick_first_model_id(client)
    chunks = []
    for ev in client.chat.completions.stream(
        model=model_id,
        messages=[{"role": "user", "content": "Stream the word hello"}],
        temperature=0,
        max_tokens=12,
    ):
        if ev.delta:
            chunks.append(ev.delta)
    text = "".join(chunks)
    assert len(text) > 0


def test_invalid_api_key_raises():
    client = Apertus(api_key="invalid-key-123")
    with pytest.raises(ApertusAPIError) as ei:
        client.models.list()
    assert ei.value.status_code in (401, 403)


def test_invalid_api_key_chat_raises():
    client = Apertus(api_key="invalid-key-123")
    with pytest.raises(ApertusAPIError) as ei:
        client.chat.completions.create(
            model="does-not-matter",
            messages=[{"role": "user", "content": "Hello"}],
        )
    assert ei.value.status_code in (401, 403)
