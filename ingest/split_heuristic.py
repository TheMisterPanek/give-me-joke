import re

_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[\u0410-\u042fA-Z"\'—\-])')

MIN_JOKE_LEN = 20
MAX_JOKE_LEN = 800


def split_jokes(text: str, target_len: int = 150) -> list[str]:
    """Group sentences into joke-sized chunks. No structural markers exist
    for joke boundaries in this source, so this is a crude heuristic:
    accumulate sentences until target_len is reached, then start a new
    joke. Boundaries will often land mid-joke or merge unrelated ones."""
    sentences = [s.strip() for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]

    jokes = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        current.append(sentence)
        current_len += len(sentence)
        if current_len >= target_len:
            jokes.append(" ".join(current))
            current = []
            current_len = 0
    if current:
        jokes.append(" ".join(current))

    return jokes


def is_probably_joke(text: str) -> bool:
    return MIN_JOKE_LEN <= len(text) <= MAX_JOKE_LEN
