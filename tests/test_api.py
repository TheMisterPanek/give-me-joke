from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from api import create_app
from retrieval import Joke


def fake_store():
    store = Mock()
    store.__len__ = Mock(return_value=15)
    return store


def test_http_contract_and_shared_retrieval(monkeypatch):
    monkeypatch.delenv("JOKER_API_KEY", raising=False)
    store = fake_store()
    scores = {"example": 12}
    with TestClient(create_app(store, scores)) as client:
        assert client.get("/health").json() == {"status": "ok", "entries": 15}
        with patch("api.find_joke", return_value=Joke("Joke", 0.7, 12)) as find:
            response = client.post("/joke", json={"query": "  broken build  "})
        assert response.status_code == 200
        assert response.json() == {"text": "Joke", "similarity": 0.7, "reactions": 12}
        find.assert_called_once_with(store, "broken build", scores)


@pytest.mark.parametrize("body", [{}, {"query": " "}, {"query": "x" * 4001}, {"query": 7}])
def test_invalid_query_does_not_call_ollama(body, monkeypatch):
    monkeypatch.delenv("JOKER_API_KEY", raising=False)
    with TestClient(create_app(fake_store(), {})) as client, patch("api.find_joke") as find:
        assert client.post("/joke", json=body).status_code == 422
        find.assert_not_called()


def test_auth_and_errors_do_not_expose_exception_details(monkeypatch):
    monkeypatch.setenv("JOKER_API_KEY", "test-key")
    with TestClient(create_app(fake_store(), {})) as client:
        with patch("api.find_joke") as find:
            assert client.post("/joke", json={"query": "topic"}).status_code == 401
            find.assert_not_called()
        headers = {"Authorization": "Bearer test-key"}
        with patch("api.find_joke", side_effect=RuntimeError("secret-in-error")):
            response = client.post("/joke", headers=headers, json={"query": "topic"})
            assert response.status_code == 503
            assert "secret-in-error" not in response.text
        with patch("api.find_joke", return_value=None):
            assert client.post("/joke", headers=headers, json={"query": "topic"}).status_code == 404


def test_empty_index_fails_at_startup(monkeypatch):
    monkeypatch.delenv("JOKER_API_KEY", raising=False)
    from store import VectorStore

    with pytest.raises(RuntimeError, match="Index is empty"):
        with TestClient(create_app(VectorStore(), {})):
            pass
