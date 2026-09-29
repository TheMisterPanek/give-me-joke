#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -f .env ]]; then
    echo 'Create .env with TELEGRAM_BOT_TOKEN.' >&2
    exit 1
fi
chmod 600 .env
podman run -d --name joker-bot --restart=unless-stopped \
    --env-file .env \
    --volume "$PWD/data/store:/app/data/store:ro" \
    --volume joker-ollama-models:/models:U \
    --read-only --tmpfs /tmp:rw,nosuid,size=128m \
    --cap-drop=all --security-opt=no-new-privileges \
    localhost/joker-bot-vps:latest
