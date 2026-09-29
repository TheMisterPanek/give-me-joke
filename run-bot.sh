#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -f .env ]]; then
    echo 'Create .env from .env.example and set TELEGRAM_BOT_TOKEN.' >&2
    exit 1
fi
chmod 600 .env
podman run -d --name joker-bot --restart=unless-stopped \
    --network=host --env-file .env \
    --volume "$PWD/data/store:/app/data/store:ro" \
    --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m \
    --cap-drop=all --security-opt=no-new-privileges \
    localhost/joker-bot:latest
