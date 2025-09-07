"""
conversation_demo.py
---------------------

A simple, terminal-based conversation demo using the local
`apertus` Python client to talk to the Apertus (Public AI Gateway) inference API.


Notes
- If you omit --api-key, the script will use the APERTUS_API_KEY env var.
- Press Ctrl+C or type /exit to quit.
- Type /help in the REPL to see available runtime commands.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Dict, Optional

from apertus import Apertus, ApertusAPIError


PREFERRED_MODEL = "swiss-ai/apertus-70b-instruct"


def choose_model(client: Apertus, preferred: Optional[str] = None) -> str:
    """Pick a model ID to use.

    1) If a preferred model is provided and available to your key, use it.
    2) Otherwise, pick the first model exposed by /v1/models.

    This is helpful because model availability can vary per key/account.
    """
    models = client.models.list()
    ids = [m.id for m in models.data if getattr(m, "id", None)]
    if not ids:
        raise RuntimeError("No models available for this API key.")

    if preferred and preferred in ids:
        return preferred

    # Try to find a close match first (prefers 70B instruct if present under different name)
    for candidate in ids:
        cid = candidate.lower()
        if "apertus" in cid and "instruct" in cid:
            return candidate

    # Fallback: the first available model
    return ids[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Terminal conversation with Apertus models")
    parser.add_argument("--api-key", default=os.getenv("APERTUS_API_KEY"), help="API key or use APERTUS_API_KEY env var")
    parser.add_argument("--model", default=PREFERRED_MODEL, help=f"Preferred model id, default: {PREFERRED_MODEL}")
    parser.add_argument("--system", default=None, help="Optional system prompt to steer behavior")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature (0-2)")
    parser.add_argument("--max-tokens", type=int, default=512, help="Max tokens for each reply")
    parser.add_argument("--base-url", default=os.getenv("APERTUS_BASE_URL", "https://api.publicai.co"), help="Override base URL")
    parser.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout in seconds")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming replies")
    return parser


def print_help() -> None:
    print(
        """
Commands:
  /help                  Show this help
  /exit                  Quit the demo
  /clear                 Clear the conversation history (keeps system prompt)
  /model <model_id>      Switch to a different model id (must be available)

Tips:
  - Use a short first message to test connectivity (e.g., "Hello!").
  - If you see authorization errors, ensure APERTUS_API_KEY is set or pass --api-key.
  - If a preferred model isn't available, the demo falls back to the first model.
        """.strip()
    )


def main() -> int:
    args = build_parser().parse_args()

    # Create a client. If api_key is None or empty, Apertus() will try APERTUS_API_KEY env var.
    try:
        client = Apertus(api_key=args.api_key, base_url=args.base_url, timeout=args.timeout)
    except ValueError as e:
        # Likely missing API key.
        print(f"Error: {e}")
        print("Set APERTUS_API_KEY or pass --api-key.")
        return 1

    # Choose a model that's actually available to your key. This avoids 400s for invalid model ids.
    try:
        model_id = choose_model(client, args.model)
    except ApertusAPIError as e:
        print(f"Failed to list models: {e}")
        return 1
    except Exception as e:
        print(f"Failed to choose model: {e}")
        return 1

    # Build the conversation history in OpenAI-like message format.
    # We'll maintain a list of dicts like {"role": "user"|"assistant"|"system", "content": str}
    messages: List[Dict[str, str]] = []
    if args.system:
        messages.append({"role": "system", "content": args.system})

    print("\nApertus Terminal Chat Demo")
    print(f"Using model: {model_id}")
    if args.system:
        print(f"System prompt set.")
    print("Type /help for commands. Press Ctrl+C to quit.\n")

    try:
        while True:
            try:
                user = input("You: ").strip()
            except EOFError:
                print()
                break

            if not user:
                continue

            # Handle simple slash-commands to control the session
            if user == "/exit":
                break
            if user == "/help":
                print_help()
                continue
            if user == "/clear":
                # keep the system prompt if any
                messages = [m for m in messages if m["role"] == "system"]
                print("History cleared.")
                continue
            if user.startswith("/model "):
                _, _, new_model = user.partition(" ")
                new_model = new_model.strip()
                if not new_model:
                    print("Usage: /model <model_id>")
                    continue
                try:
                    # Validate new model exists for this key
                    model_id = choose_model(client, new_model)
                    print(f"Switched to model: {model_id}")
                except Exception as e:
                    print(f"Failed to switch model: {e}")
                continue

            # Append the user's message to the conversation history
            messages.append({"role": "user", "content": user})

            print("Assistant: ", end="", flush=True)
            try:
                if args.no_stream:
                    # Non-streaming mode: single response payload
                    resp = client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        temperature=args.temperature,
                        max_tokens=args.max_tokens,
                    )
                    text = resp.choices[0].message.content
                    print(text)
                    messages.append({"role": "assistant", "content": text})
                else:
                    # Streaming mode: print tokens as they arrive, then save the final text to history
                    chunks: List[str] = []
                    for ev in client.chat.completions.stream(
                        model=model_id,
                        messages=messages,
                        temperature=args.temperature,
                        max_tokens=args.max_tokens,
                    ):
                        if ev.delta:
                            print(ev.delta, end="", flush=True)
                            chunks.append(ev.delta)
                    print()  # newline after stream
                    final_text = "".join(chunks)
                    messages.append({"role": "assistant", "content": final_text})
            except ApertusAPIError as e:
                print(f"\n[API error {e.status_code}] {e.message}")
            except KeyboardInterrupt:
                print("\nInterrupted. Type /exit to quit.")
            except Exception as e:
                print(f"\nUnexpected error: {e}")

    except KeyboardInterrupt:
        pass

    print("\nGoodbye!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
