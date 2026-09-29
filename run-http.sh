#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
env_options=()
if [[ -f .env ]]; then
    chmod 600 .env
    env_options=(--env-file .env)
fi
podman run -d --name joker-http --restart=unless-stopped \
    "${env_options[@]}" --env JOKER_MODE=http --env JOKER_HTTP_PORT=8080 \
    --publish "127.0.0.1:${JOKER_HTTP_PORT:-8080}:8080" \
    --volume "$PWD/data/store:/app/data/store:ro" \
    --volume joker-ollama-models:/models:U \
    --read-only --tmpfs /tmp:rw,nosuid,size=128m \
    --cap-drop=all --security-opt=no-new-privileges \
    localhost/joker-bot-vps:latest
