import hashlib
import json
import os
from pathlib import Path

from store import DEFAULT_STORE_DIR

POSITIVE_REACTIONS = {"🤡", "❤", "❤️", "👍", "😁", "😂", "🤣", "🔥", "🥰"}


def text_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scores_path() -> Path:
    return Path(os.environ.get("JOKER_STORE_DIR", DEFAULT_STORE_DIR)) / "reactions.json"


def load_scores() -> dict[str, int]:
    path = scores_path()
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def scores_from_export(export: dict) -> dict[str, int]:
    scores = {}
    for message in export["messages"]:
        if message.get("type") != "message":
            continue
        raw = message.get("text", "")
        parts = [raw] if isinstance(raw, str) else raw
        text = "".join(part if isinstance(part, str) else part.get("text", "") for part in parts).strip()
        if not text:
            continue
        score = sum(
            reaction.get("count", 0)
            for reaction in message.get("reactions", [])
            if reaction.get("emoji") in POSITIVE_REACTIONS
        )
        key = text_key(text)
        # Duplicate/reposted texts use the most popular post, not a sum of reposts.
        scores[key] = max(scores.get(key, 0), score)
    return scores


def save_scores(scores: dict[str, int]) -> None:
    path = scores_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(scores, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def build_scores(export_path: str = "jokes.json") -> dict[str, int]:
    with open(export_path, encoding="utf-8") as source:
        scores = scores_from_export(json.load(source))
    save_scores(scores)
    return scores


if __name__ == "__main__":
    import sys

    result = build_scores(sys.argv[1] if len(sys.argv) > 1 else "jokes.json")
    print(f"Saved scores for {len(result)} texts to {scores_path()}")
