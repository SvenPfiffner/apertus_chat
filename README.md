# 🚀 Apertus Python Client

A clean and modular Python client for interfacing with the publicai endpoint of the new swiss apertus model. Built in the style of the OpenAI package:

* **Easy-to-use** clients — both sync & async
* **Versatile** chat completions — streaming and non-streaming
* **Typed data models** — powered by Pydantic
* **Small, extensible** codebase

---

## Installation

From the repository root:

```bash
pip install -e .
```

**Requirements**: Python 3.8+

---

## Setup

Set up your API credentials:

```bash
export APERTUS_API_KEY=YOUR_KEY
```

Or pass the key directly:

```python
client = Apertus(api_key="YOUR_KEY")
```

---

## Quickstart Examples

### Sync Usage

```python
from apertus import Apertus

client = Apertus()  # Reads from APERTUS_API_KEY by default

# List available models
models = client.models.list()
print([m.id for m in models.data][:5])
model_id = models.data[0].id

# Standard chat completion
resp = client.chat.completions.create(
    model=model_id,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
    temperature=0.2,
)
print(resp.choices[0].message.content)

# Streaming completion
for ev in client.chat.completions.stream(
    model=model_id,
    messages=[{"role": "user", "content": "Stream a short greeting."}],
    temperature=0.2,
):
    if ev.delta:
        print(ev.delta, end="", flush=True)
print()
```

---

### Async Usage

```python
import asyncio
from apertus import AsyncApertus

async def main():
    client = AsyncApertus()
    models = await client.models.list()
    model_id = models.data[0].id

    resp = await client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": "Hello from async!"}],
    )
    print(resp.choices[0].message.content)

asyncio.run(main())
```

---

## Examples Directory

* **Notebook (`examples.ipynb`)**: Try listing models, sync/async usage, streaming, batching via pandas + tqdm, visualization, and saving artifacts.
* **Terminal Demo (`conversation_demo.py`)**: A cozy REPL with history, streaming output, and model fallback. Run with:

```bash
python conversation_demo.py --api-key "$APERTUS_API_KEY"
```

---

## Error Handling

Non-2xx API responses raise an `ApertusAPIError`, which includes:

* `status_code`
* `message`
* `url`
* `payload` (if available)

---

## Development

* Develop in editable mode:

  ```bash
  pip install -e .
  ```
* Run tests:

  ```bash
  pytest -q
  ```
* Project structure:

  * `apertus/` — core client, HTTP layer, Pydantic models
  * `tests/` — unit and integration tests

---

## License & Disclaimer

Licensed under **MIT**.

> This is an independent, hobby-project effort, **not affiliated** with the Apertus team or the Public AI group. Use at your own risk—but enjoy making Apertus accessible! ✨

---

## Citations & References

* **Apertus** — A fully open, transparent, multilingual large language model developed by EPFL, ETH Zurich, and CSCS ([ETH Zürich][1], [Swiss AI][2]).

* **Public AI Gateway** — A nonprofit, open-source inference service that helps make public and sovereign AI models more accessible ([PublicAI][3]).

---

[1]: https://ethz.ch/en/news-and-events/eth-news/news/2025/09/press-release-apertus-a-fully-open-transparent-multilingual-language-model.html?utm_source=chatgpt.com "Apertus: a fully open, transparent, multilingual language ..."
[2]: https://www.swiss-ai.org/apertus?utm_source=chatgpt.com "Apertus - Swiss AI Initiative"
[3]: https://publicai.co/?utm_source=chatgpt.com "Public AI Inference Utility"
