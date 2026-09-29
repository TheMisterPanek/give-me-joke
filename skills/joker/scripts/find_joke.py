#!/usr/bin/env python3
"""Self-contained Joker client; Python standard library only."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Find a joke through the Joker HTTP API")
    parser.add_argument("query", nargs="?", help="Short topic; read stdin when omitted")
    args = parser.parse_args()
    query = (args.query if args.query is not None else sys.stdin.read()).strip()
    if not 1 <= len(query) <= 4000:
        print("Query must contain 1–4000 characters", file=sys.stderr)
        return 1
    base_url = os.environ.get("JOKER_API_URL", "http://127.0.0.1:8080").rstrip("/")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("JOKER_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(
        base_url + "/joke", data=json.dumps({"query": query}).encode("utf-8"), headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
        if not isinstance(result, dict) or not isinstance(result.get("text"), str):
            raise ValueError("Invalid response")
    except urllib.error.HTTPError as error:
        print(f"Joker API returned HTTP {error.code}", file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("Joker API unavailable or invalid response", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
