from unittest.mock import MagicMock, patch

import embeddings


def test_embed_calls_client_with_model_and_input():
    fake_response = MagicMock(embeddings=[[0.1, 0.2], [0.3, 0.4]])
    fake_client = MagicMock()
    fake_client.embed.return_value = fake_response

    with patch("embeddings._client", return_value=fake_client):
        result = embeddings.embed(["foo", "bar"])

    fake_client.embed.assert_called_once_with(
        model=embeddings.DEFAULT_MODEL, input=["foo", "bar"]
    )
    assert result == [[0.1, 0.2], [0.3, 0.4]]


def test_embed_uses_model_from_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_EMBED_MODEL", "custom-model")
    fake_response = MagicMock(embeddings=[[1.0]])
    fake_client = MagicMock()
    fake_client.embed.return_value = fake_response

    with patch("embeddings._client", return_value=fake_client):
        embeddings.embed(["foo"])

    fake_client.embed.assert_called_once_with(model="custom-model", input=["foo"])
