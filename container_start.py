"""Supervise a local Ollama server and a Telegram bot or HTTP API."""

import os
import signal
import subprocess
import sys
import time
import urllib.request


def main() -> None:
    # Both processes share loopback inside the container, independent of .env.
    os.environ["OLLAMA_HOST"] = "127.0.0.1:11434"
    model = os.environ.get("OLLAMA_EMBED_MODEL", "qwen3-embedding:0.6b")
    mode = os.environ.get("JOKER_MODE", "telegram")
    if mode not in {"telegram", "http"}:
        raise SystemExit("JOKER_MODE must be telegram or http")
    children = []

    def stop(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        server = subprocess.Popen(["ollama", "serve"])
        children.append(server)
        for _ in range(120):
            if server.poll() is not None:
                raise RuntimeError("Ollama exited before the service started")
            try:
                with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1):
                    break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError("Ollama did not start within 120 seconds")

        # Existing models are reused; first startup downloads the selected model.
        available = subprocess.run(["ollama", "show", model], capture_output=True)
        if available.returncode:
            print(f"Downloading model {model}…", flush=True)
            pull = subprocess.Popen(["ollama", "pull", model])
            children.append(pull)
            if pull.wait():
                raise RuntimeError("Failed to download the model")

        if sys.argv[1:] == ["--check"]:
            from retrieval import choose_joke
            from store import VectorStore
            from reactions import load_scores

            store = VectorStore.load()
            if not store:
                raise RuntimeError("Index is empty")
            print(f"Check: {len(store)} entries", flush=True)
            print(choose_joke(store, "about work", load_scores()), flush=True)
            return

        bot = subprocess.Popen([sys.executable, "api.py" if mode == "http" else "bot.py"])
        children.append(bot)
        while True:
            for child in (server, bot):
                if child.poll() is not None:
                    raise RuntimeError(f"Process {child.args[0]} exited: {child.returncode}")
            time.sleep(1)
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in reversed(children):
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
