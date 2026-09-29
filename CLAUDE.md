# Development notes

Joker retrieves existing jokes from a user's private collection. Telegram,
HTTP, and MCP share the policy in `retrieval.py`: filter candidates, select
15 by cosine similarity, rank by positive reactions, choose randomly among five.

- `ingest/dataset.py`: Telegram by default, JSONL, and custom `module:callable`
  or `file.py:callable` adapters. Records contain text, tags, and reaction count.
- `store.py`: normalized float32 vectors; embeddings calculated only for new texts.
- `reactions.py`: separate score map keyed by a hash of the normalized text.
- `api.py`: `/health`, `/joke`, optional bearer key; loads the index once.
- `bot.py`: Telegram polling frontend.
- `mcp_server.py`: stdio adapter to HTTP; does not load another index.
- `skills/joker`: portable agent skill and a standard-library HTTP helper.
- `Containerfile.vps`: CPU Ollama plus either Telegram or HTTP, selected by `JOKER_MODE`.

Run `uv run pytest -q`. Regenerate `requirements-bot.txt` with `uv export`
after dependency changes. Dataset/parser examples are generated under `data/`.

Do not include private dumps, the index, reaction maps, tokens, archive bundles,
or source channel/collection identifiers in publishable files. Do not copy real
jokes into test fixtures. Technical dependency and model identifiers are required
for reproducible setup; they are separate from source collection branding.

Keep imports and skill/API clients free of expensive indexing work. Existing
vectors must use the same embedding model as queries. Filters and reaction
ranking are applied without reindexing. Preserve full post boundaries.
