import sys

from ingest.split_heuristic import is_probably_joke, split_jokes
from ingest.text_book import parse_book
from store import VectorStore

DEFAULT_BOOK_PATH = "data/raw/jokes.txt"


def build(book_path: str = DEFAULT_BOOK_PATH) -> VectorStore:
    store = VectorStore.load()
    existing_texts = store.texts

    sections = parse_book(book_path)
    for i, section in enumerate(sections, start=1):
        jokes = [j for j in split_jokes(section.text) if is_probably_joke(j)]

        new_jokes = [j for j in jokes if j not in existing_texts]
        if new_jokes:
            store.add(new_jokes, tags=[[section.title]] * len(new_jokes))
            existing_texts.update(new_jokes)
            store.save()

        print(
            f"[{i}/{len(sections)}] {section.title}: "
            f"{len(jokes)} split, {len(new_jokes)} new, store size {len(store)}",
            file=sys.stderr,
        )

    return store


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOOK_PATH
    build(book_path=path)
