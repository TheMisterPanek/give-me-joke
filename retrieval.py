"""Shared retrieval policy for Telegram, HTTP, and MCP clients."""

import random
import re
from dataclasses import dataclass

from reactions import text_key
from store import Entry, VectorStore


@dataclass
class Joke:
    text: str
    similarity: float
    reactions: int


def is_joke_candidate(entry: Entry) -> bool:
    text = re.sub(r"#\w+", "", entry.text).strip()
    if len(text) < 40 or len(re.findall(r"[^\W\d_]+", text)) < 7:
        return False
    if not any(char in text for char in ".!?…\n"):
        return False
    # Keep Russian spam markers for existing collections; support English too.
    return not re.search(
        r"@|https?://|t\.me/|subscrib\w*|advertis\w*|"
        r"\u043f\u043e\u0434\u043f\u0438\u0448\w*|\u0440\u0435\u043a\u043b\u0430\u043c\w*",
        text, re.IGNORECASE,
    )


def find_joke(store: VectorStore, query: str, reaction_scores: dict[str, int] | None = None) -> Joke | None:
    results = store.search(query, k=15, predicate=is_joke_candidate)
    if not results:
        return None
    scores = reaction_scores or {}
    # Stable sorting keeps semantic similarity as the tiebreaker.
    finalists = sorted(results, key=lambda result: scores.get(text_key(result.entry.text), 0), reverse=True)[:5]
    result = random.choice(finalists)
    return Joke(result.entry.text, result.score, scores.get(text_key(result.entry.text), 0))


def choose_joke(store: VectorStore, query: str, reaction_scores: dict[str, int] | None = None) -> str:
    joke = find_joke(store, query, reaction_scores)
    return joke.text if joke else "The joke collection is empty."
