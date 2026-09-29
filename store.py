import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from embeddings import embed

DEFAULT_STORE_DIR = "data/store"


@dataclass
class Entry:
    text: str
    tags: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    entry: Entry
    score: float


class VectorStore:
    def __init__(self) -> None:
        self._entries: list[Entry] = []
        self._vectors: np.ndarray = np.zeros((0, 0), dtype=np.float32)

    def add(self, texts: list[str], tags: list[list[str]] | None = None) -> None:
        if not texts:
            return
        if tags is None:
            tags = [[] for _ in texts]

        new_vectors = np.array(embed(texts), dtype=np.float32)
        new_vectors /= np.linalg.norm(new_vectors, axis=1, keepdims=True)

        if self._vectors.size == 0:
            self._vectors = new_vectors
        else:
            self._vectors = np.vstack([self._vectors, new_vectors])

        self._entries.extend(Entry(text=t, tags=tg) for t, tg in zip(texts, tags))

    def search(
        self, query: str, k: int = 5,
        predicate: Callable[[Entry], bool] | None = None,
    ) -> list[SearchResult]:
        if not self._entries:
            return []

        query_vec = np.array(embed([query])[0], dtype=np.float32)
        query_vec /= np.linalg.norm(query_vec)

        scores = self._vectors @ query_vec
        ranked = np.argsort(-scores)
        top_indices = [
            i for i in ranked if predicate is None or predicate(self._entries[i])
        ][:k]

        return [SearchResult(entry=self._entries[i], score=float(scores[i])) for i in top_indices]

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def texts(self) -> set[str]:
        return {e.text for e in self._entries}

    def save(self, path: str | None = None) -> None:
        store_dir = Path(path or os.environ.get("JOKER_STORE_DIR", DEFAULT_STORE_DIR))
        store_dir.mkdir(parents=True, exist_ok=True)

        np.save(store_dir / "embeddings.npy", self._vectors)
        with open(store_dir / "entries.jsonl", "w", encoding="utf-8") as f:
            for entry in self._entries:
                f.write(json.dumps({"text": entry.text, "tags": entry.tags}, ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, path: str | None = None) -> "VectorStore":
        store_dir = Path(path or os.environ.get("JOKER_STORE_DIR", DEFAULT_STORE_DIR))
        store = cls()

        entries_path = store_dir / "entries.jsonl"
        if not entries_path.exists():
            return store

        with open(entries_path, encoding="utf-8") as f:
            store._entries = [
                Entry(text=row["text"], tags=row["tags"])
                for row in (json.loads(line) for line in f if line.strip())
            ]
        store._vectors = np.load(store_dir / "embeddings.npy")

        return store
