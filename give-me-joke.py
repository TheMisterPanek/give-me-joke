import argparse

from store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Find jokes by query in the local vector index.")
    parser.add_argument("query", help="search topic, for example 'about programmers'")
    parser.add_argument("-k", type=int, default=5, help="number of jokes to return (default: 5)")
    args = parser.parse_args()

    store = VectorStore.load()
    if not store:
        print("The index is empty. First run: uv run python -m ingest.dataset <export.json>")
        return

    for result in store.search(args.query, k=args.k):
        print(f"[{result.score:.3f}] {', '.join(result.entry.tags)}")
        print(result.entry.text)
        print()


if __name__ == "__main__":
    main()
