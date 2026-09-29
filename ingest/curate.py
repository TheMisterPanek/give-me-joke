import json
import os
import sys

from ollama import Client

from store import Entry

DEFAULT_CHAT_MODEL = "qwen3:1.7b"
DEFAULT_CHUNK_CHARS = 2000

_SYSTEM_PROMPT = (
    "You are given an excerpt from a joke collection. Split it into complete "
    "standalone jokes. Discard incomplete fragments, "
    "tables of contents, author signatures, and service text. Preserve the source language. "
    "Return only a JSON array of strings, each containing one complete joke, without "
    "numbering or comments. If there are no complete jokes, return []."
)


def _client() -> Client:
    return Client(host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))


def chunk_text(text: str, max_chars: int = DEFAULT_CHUNK_CHARS) -> list[str]:
    words = text.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > max_chars and current:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
        current.append(word)
        current_len += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def curate_chunk(chunk: str) -> list[str]:
    model = os.environ.get("OLLAMA_CHAT_MODEL", DEFAULT_CHAT_MODEL)
    response = _client().chat(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": chunk},
        ],
        format={"type": "array", "items": {"type": "string"}},
    )
    try:
        jokes = json.loads(response.message.content)
        if isinstance(jokes, dict):
            jokes = next((v for v in jokes.values() if isinstance(v, list)), None)
        if not isinstance(jokes, list):
            raise ValueError("expected a JSON array (optionally wrapped in an object)")
        return [j for j in jokes if isinstance(j, str) and j.strip()]
    except (json.JSONDecodeError, ValueError) as e:
        print(f"curate_chunk: could not parse model output ({e}), skipping chunk", file=sys.stderr)
        return []


def curate_text(text: str, tags: list[str], max_chars: int = DEFAULT_CHUNK_CHARS) -> list[Entry]:
    entries = []
    for chunk in chunk_text(text, max_chars=max_chars):
        for joke in curate_chunk(chunk):
            entries.append(Entry(text=joke, tags=tags))
    return entries
