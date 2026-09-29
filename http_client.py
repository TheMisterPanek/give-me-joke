"""Small HTTP client shared by the skill helper and MCP adapter."""

import json
import os
import urllib.error
import urllib.request


def request_joke(query: str) -> dict:
    query = query.strip()
    if not 1 <= len(query) <= 4000:
        raise ValueError("Query must contain 1–4000 characters")
    url = os.environ.get("JOKER_API_URL", "http://127.0.0.1:8080").rstrip("/")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("JOKER_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(
        url + "/joke", data=json.dumps({"query": query}).encode("utf-8"), headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Joker API returned HTTP {error.code}") from None
    except (OSError, ValueError):
        raise RuntimeError("Joker API unavailable or invalid response") from None
    if not isinstance(result, dict) or not isinstance(result.get("text"), str):
        raise RuntimeError("Joker API returned an invalid response")
    return result
