"""Generate a tiny synthetic Telegram-style input under gitignored data/."""

import json
from pathlib import Path

TEXTS = [
    "A developer asked the kettle to boil water. It replied: first update the firmware and accept the terms of boiling.",
    "— Why are the tests red again?\n— They are celebrating autumn.\n— When will they turn green?\n— When we fix the calendar.",
    "A developer removed every unnecessary dependency. An hour later, only an empty folder, a cup of coffee, and a dependency on coffee remained.",
]


def main() -> None:
    path = Path("data/demo/export.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    export = {"name": "Synthetic demo", "messages": [
        {"id": number, "type": "message", "text": text,
         "reactions": [{"type": "emoji", "emoji": "👍", "count": number}]}
        for number, text in enumerate(TEXTS, start=1)
    ]}
    path.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
