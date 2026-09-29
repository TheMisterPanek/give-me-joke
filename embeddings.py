import os
from functools import lru_cache

from ollama import Client

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen3-embedding:0.6b"


@lru_cache(maxsize=1)
def _client() -> Client:
    return Client(host=os.environ.get("OLLAMA_HOST", DEFAULT_HOST))


def embed(texts: list[str]) -> list[list[float]]:
    model = os.environ.get("OLLAMA_EMBED_MODEL", DEFAULT_MODEL)
    response = _client().embed(model=model, input=texts)
    return response.embeddings
