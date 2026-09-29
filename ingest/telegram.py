"""Index text posts from a Telegram JSON export, preserving post boundaries."""

import argparse
import json
import sys
from pathlib import Path

from store import Entry, VectorStore


def parse_export(path: str) -> list[Entry]:
    with open(path, encoding="utf-8") as source:
        export = json.load(source)
    entries = []
    seen = set()
    for message in export["messages"]:
        if message.get("type") != "message":
            continue
        raw = message.get("text", "")
        parts = [raw] if isinstance(raw, str) else raw
        text = "".join(
            part if isinstance(part, str) else part.get("text", "")
            for part in parts
        ).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        tags = [export.get("name", Path(path).stem)]
        tags.extend(
            entity["text"]
            for entity in message.get("text_entities", [])
            if entity.get("type") == "hashtag"
        )
        entries.append(Entry(text=text, tags=list(dict.fromkeys(tags))))
    return entries


def build(path: str = "jokes.json", batch_size: int = 32) -> VectorStore:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    store = VectorStore.load()
    existing = store.texts
    entries = [entry for entry in parse_export(path) if entry.text not in existing]
    print(f"New messages: {len(entries)}, already indexed: {len(store)}", file=sys.stderr, flush=True)
    for start in range(0, len(entries), batch_size):
        batch = entries[start:start + batch_size]
        store.add([entry.text for entry in batch], [entry.tags for entry in batch])
        store.save()
        print(f"Indexed {min(start + batch_size, len(entries))}/{len(entries)}, total {len(store)}", file=sys.stderr, flush=True)
    return store


def main() -> None:
    parser = argparse.ArgumentParser(description="Index jokes from a Telegram export.")
    parser.add_argument("path", nargs="?", default="jokes.json")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    build(args.path, args.batch_size)


if __name__ == "__main__":
    main()
