"""Example adapter: CSV columns body, category, likes -> Joker records."""

import csv


def parse(path: str):
    with open(path, newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if not row["body"].strip():
                continue
            yield {
                "text": row["body"],
                "tags": [row["category"]] if row.get("category") else [],
                "reactions": int(row.get("likes") or 0),
            }
