"""HTTP interface: python api.py (loopback by default)."""

import logging
import os
import secrets
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from reactions import load_scores
from retrieval import Joke, find_joke
from store import VectorStore

logger = logging.getLogger(__name__)


class JokeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(min_length=1, max_length=4000)


def create_app(store: VectorStore | None = None, reaction_scores: dict[str, int] | None = None) -> FastAPI:
    api_key = os.environ.get("JOKER_API_KEY", "").strip()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.store = store if store is not None else VectorStore.load()
        app.state.reactions = reaction_scores if reaction_scores is not None else load_scores()
        if not app.state.store:
            raise RuntimeError("Index is empty: run python -m ingest.dataset <export.json>")
        yield

    app = FastAPI(title="Joker", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict:
        # Liveness/index readiness; does not invoke or load an Ollama model.
        return {"status": "ok", "entries": len(app.state.store)}

    @app.post("/joke", response_model=Joke)
    def joke(request: JokeRequest, authorization: str | None = Header(default=None)) -> Joke:
        if api_key and not secrets.compare_digest(
            (authorization or "").encode(), f"Bearer {api_key}".encode()
        ):
            raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"})
        try:
            result = find_joke(app.state.store, request.query, app.state.reactions)
        except Exception as error:
            logger.error("Search unavailable: %s", type(error).__name__)
            raise HTTPException(status_code=503, detail="Search is temporarily unavailable") from None
        if result is None:
            raise HTTPException(status_code=404, detail="No matching jokes found")
        return result

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("JOKER_HTTP_HOST", "127.0.0.1"),
                port=int(os.environ.get("JOKER_HTTP_PORT", "8080")))
