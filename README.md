# joker

[English](README.md) | [Русский](README.ru.md) | [Polski](README.pl.md)

Retrieve existing jokes by meaning from your own collection. The same algorithm
is available through a Telegram bot, HTTP API, MCP tool, and ready-to-use agent skill.

Joker finds 15 texts by cosine similarity, ranks them by positive reactions, and
randomly returns one of the top five. It does not generate jokes or require literal
query keywords. See [research notes and limitations](docs/research.md).

## Data and licensing

This repository contains MIT-licensed code, documentation, adapters, and synthetic
test examples. It does not include real datasets, source channel/collection names,
a prebuilt index, or credentials. Bring your own collection.

Keep sources in `data/raw/`, the index in `data/store/`, and private parsers in
`data/parsers/`. `data/`, `.env`, common dataset formats, and archives are gitignored.
The index contains source texts, so do not publish it either. Dependency names
are included for reproducible setup; downloaded models have their own licenses.

## Quick start

You need Python 3.12+, uv, and a running Ollama server. Use the same embedding
model for indexing and queries: `qwen3-embedding:0.6b` by default.

```bash
uv sync
ollama pull qwen3-embedding:0.6b
# Run ollama serve in another session or as a service.
uv run python -m ingest.dataset data/raw/export.json
```

The default parser reads a Telegram JSON message export. Formatting fragments are
joined; each post becomes one record. Empty/service messages and exact duplicates
are skipped. Reaction scores are extracted automatically. Indexing saves batches;
reruns only embed new texts and update maximum reaction scores.

Validate input without Ollama or index changes:

```bash
uv run python -m ingest.dataset data/raw/export.json --validate-only
```

Try a generated synthetic example in a separate index:

```bash
uv run python tools/make_demo.py
JOKER_STORE_DIR=data/demo/store uv run python -m ingest.dataset data/demo/export.json
JOKER_STORE_DIR=data/demo/store uv run python api.py
```

Messages and developer-facing output are in English. Retrieved jokes keep their
source language; translating the software does not translate or reindex your data.

## HTTP API

With an existing index:

```bash
uv run python api.py
```

The default address is `http://127.0.0.1:8080`. No Telegram token is needed.

```bash
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/joke \
  -H 'Content-Type: application/json' \
  -d '{"query":"a bug that refuses to be fixed"}'
```

`POST /joke` returns:

```json
{"text":"The joke text…", "similarity":0.72, "reactions":35}
```

`query` must contain 1–4000 characters. Error codes: `422` invalid input, `401`
invalid key, `404` no eligible jokes, `503` search/Ollama unavailable.
`GET /health` checks the process and loaded index without invoking the model.
Interactive API documentation is available at `/docs`.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `JOKER_STORE_DIR` | `data/store` | Index and reaction scores |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama address |
| `OLLAMA_EMBED_MODEL` | `qwen3-embedding:0.6b` | Embedding model |
| `JOKER_HTTP_HOST` | `127.0.0.1` | HTTP bind address |
| `JOKER_HTTP_PORT` | `8080` | HTTP port |
| `JOKER_API_KEY` | empty | Optional bearer key for `/joke` |

If `JOKER_API_KEY` is set, send `Authorization: Bearer <key>`. Load settings from
a file with `uv run --env-file .env python api.py`. For external access, use a key
and HTTPS through a reverse proxy.

## Telegram bot

With Ollama running on your computer:

```bash
cp .env.example .env
# Set TELEGRAM_BOT_TOKEN in .env.
uv run --env-file .env python bot.py
```

The bot replies to text messages. `/start` and `/help` explain how it works.
To receive all messages in groups, disable privacy mode through the bot creation
service. Run only one polling instance per token.

## Podman containers

Build the index on the host first; containers mount it read-only. Data and `.env`
are excluded from the image. Build the base image:

```bash
podman build -t localhost/joker-bot:latest -f Containerfile .
```

Telegram with host Ollama on Linux:

```bash
bash run-bot.sh
podman logs -f joker-bot
```

For Telegram or HTTP with Ollama inside the container:

```bash
podman build -t localhost/joker-bot-vps:latest -f Containerfile.vps .
```

Choose one mode:

```bash
# Telegram: .env with TELEGRAM_BOT_TOKEN is required.
bash run-bot-vps.sh
podman logs -f joker-bot

# Or HTTP: .env is optional; no Telegram token is needed.
bash run-http.sh
podman logs -f joker-http
curl http://127.0.0.1:8080/health
```

HTTP is published only on the host loopback interface. To use another port, run
`JOKER_HTTP_PORT=8081 bash run-http.sh`. These are separate modes; running both
containers is unnecessary for a basic setup.

Bundled Ollama uses CPU inference and downloads the model on first startup.
The `joker-ollama-models` volume keeps it across container recreation. Ollama's
port is not published; `OLLAMA_HOST` is set to the container's internal loopback.
Set `OLLAMA_KEEP_ALIVE=0` in `.env` to unload the model after each request;
Ollama's default is five minutes. The bot/API and index remain in memory.

Stop with `podman stop joker-bot` or `podman stop joker-http`; restart with
`podman start <name>`. After changing `.env`, code, or reaction scores, stop and
remove the container, then rerun its launch script. Configure systemd/Quadlet
for startup after a server reboot.

Transfer to another Linux host of the same architecture:

```bash
podman save -o joker-bot-vps.tar localhost/joker-bot-vps:latest
tar -czf joker-data.tar.gz data/store run-bot-vps.sh run-http.sh
ssh user@VPS 'mkdir -p ~/joker'
scp joker-bot-vps.tar joker-data.tar.gz user@VPS:~/joker/
# For Telegram, transfer .env separately over SSH.
```

On the new host:

```bash
cd ~/joker
podman load -i joker-bot-vps.tar
tar -xzf joker-data.tar.gz
bash run-http.sh  # Or bash run-bot-vps.sh with .env.
```

The model volume is not included in `podman save`; it will download again on
the new host. The index archive is for private transfers, not public Git.

## Bring your own parser

Keep the core code unchanged. Convert your source into this record contract:

```json
{"text":"One complete joke", "tags":["topic"], "reactions":12}
```

Only `text` is required: a nonempty string. `tags` is a list of strings, default
`[]`; `reactions` is a nonnegative integer positive-reaction count, default `0`.
Unknown fields are rejected. Your adapter determines joke boundaries, source
cleanup, and how source ratings map to `reactions`.

Two options:

1. Produce JSONL with one record per line:
   `uv run python -m ingest.dataset data/raw/jokes.jsonl --parser jsonl`.
2. Write a Python function `parse(path)` that returns or yields record dictionaries.
   Use regex, CSV, XML, or other parsing tools appropriate to your input.

[examples/csv_parser.py](examples/csv_parser.py) is a working adapter for CSV
columns `body`, `category`, and `likes`. Copy it to `data/parsers/my_parser.py`,
adapt the fields, and validate before indexing:

```bash
uv run python -m ingest.dataset data/raw/source.csv \
  --parser data/parsers/my_parser.py:parse --validate-only
uv run python -m ingest.dataset data/raw/source.csv \
  --parser data/parsers/my_parser.py:parse
```

Importable modules also work: `--parser my_package.my_parser:parse`. A parser
is local executable Python code. Records are validated as batches are ingested;
if a later record fails, previously saved batches remain. Fix the input and
rerun to resume. `--batch-size` defaults to 32. Restart the service after updating scores.

## MCP and agent skill

Start the HTTP API first. The MCP adapter exposes `find_joke(context)` through
stdio and calls the API without loading a second index. Example client configuration
(replace the absolute path):

```json
{
  "mcpServers": {
    "joker": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/joker", "python", "mcp_server.py"],
      "env": {"JOKER_API_URL":"http://127.0.0.1:8080"}
    }
  }
}
```

If the API is protected, also set `JOKER_API_KEY` in the client's environment.
The tool returns `text`, `similarity`, and `reactions`.

The [Joker skill](skills/joker/SKILL.md) uses MCP or a standalone Python helper
that requires no third-party dependencies:

```bash
JOKER_API_URL=http://127.0.0.1:8080 \
  python3 skills/joker/scripts/find_joke.py "a stubborn programming bug"
```

Copy `skills/joker` into your agent's skills directory, for example:

```bash
# For an agent using ~/.claude/skills:
mkdir -p ~/.claude/skills
cp -R skills/joker ~/.claude/skills/
# Or an agent using ~/.codex/skills:
mkdir -p ~/.codex/skills
cp -R skills/joker ~/.codex/skills/
```

MCP does not add jokes automatically; the agent follows the user's instructions.
An opt-in instruction could be: “If the task remains unsolved, first explain the
result and blocker honestly. Then, if appropriate, use Joker and add one joke.
Do not stop trying to solve the task just to retrieve a joke.” The skill sends
only a short topic, not code, logs, or the entire conversation.

## Development

```bash
uv run pytest -q
uv export --frozen --no-dev --no-emit-project -o requirements-bot.txt
```

`give-me-joke.py` is a diagnostic CLI that searches the entire index and shows
similarity scores. Use the API or bot for filtered, reaction-ranked retrieval.
