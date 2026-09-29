"""Bring your own dataset/parser, with a shared record contract."""

import argparse
import importlib
import importlib.util
import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ingest.telegram import parse_export
from reactions import load_scores, save_scores, scores_from_export, text_key
from store import VectorStore


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)
    text: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    reactions: int = Field(default=0, ge=0)


def parse_jsonl(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as source:
        for number, line in enumerate(source, start=1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{number}: invalid JSON") from error


def parse_telegram(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as source:
        scores = scores_from_export(json.load(source))
    for entry in parse_export(path):
        yield {"text": entry.text, "tags": entry.tags, "reactions": scores.get(text_key(entry.text), 0)}


def read_records(path: str, parser: str = "telegram") -> Iterator[Record]:
    if parser in {"jsonl", "telegram"}:
        reader = parse_jsonl if parser == "jsonl" else parse_telegram
    else:
        module_name, separator, function_name = parser.partition(":")
        if not separator or not function_name:
            raise ValueError("Parser: telegram, jsonl, module:callable, or file.py:callable")
        if module_name.endswith(".py"):
            spec = importlib.util.spec_from_file_location("joker_custom_parser", Path(module_name).resolve())
            if spec is None or spec.loader is None:
                raise ValueError("Could not load the parser file")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            module = importlib.import_module(module_name)
        reader = getattr(module, function_name)
        if not callable(reader):
            raise ValueError("The parser must be callable")
    for number, row in enumerate(reader(path), start=1):
        try:
            yield Record.model_validate(row)
        except ValidationError as error:
            fields = ", ".join(".".join(map(str, item["loc"])) or "record" for item in error.errors())
            raise ValueError(f"Record {number}: invalid fields {fields}") from error


def build(records: Iterable[Record], batch_size: int = 32) -> VectorStore:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    store = VectorStore.load()
    seen = store.texts
    scores = load_scores()
    batch = []

    def flush() -> None:
        if batch:
            store.add([record.text for record in batch], [record.tags for record in batch])
            store.save()
            save_scores(scores)
            batch.clear()
            print(f"Index contains {len(store)} texts", flush=True)

    for record in records:
        key = text_key(record.text)
        scores[key] = max(scores.get(key, 0), record.reactions)
        if record.text in seen:
            continue
        seen.add(record.text)
        batch.append(record)
        if len(batch) >= batch_size:
            flush()
    flush()
    save_scores(scores)
    return store


def main() -> None:
    cli = argparse.ArgumentParser(description="Index your dataset or validate parser output")
    cli.add_argument("path")
    cli.add_argument("--parser", default="telegram", help="telegram (default), jsonl, module:callable, or file.py:callable")
    cli.add_argument("--batch-size", type=int, default=32)
    cli.add_argument("--validate-only", action="store_true", help="Validate records without Ollama or modifying the index")
    args = cli.parse_args()
    if args.batch_size < 1:
        cli.error("--batch-size must be positive")
    records = read_records(args.path, args.parser)
    if args.validate_only:
        print(f"Validated records: {sum(1 for _ in records)}")
    else:
        build(records, args.batch_size)


if __name__ == "__main__":
    main()
