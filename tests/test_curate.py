from unittest.mock import MagicMock, patch

from ingest.curate import chunk_text, curate_chunk, curate_text


def test_chunk_text_splits_on_word_boundaries_within_limit():
    text = "one two three four five"
    chunks = chunk_text(text, max_chars=12)

    assert all(len(c) <= 12 or " " not in c for c in chunks)
    assert " ".join(chunks) == text


def test_chunk_text_short_text_stays_single_chunk():
    assert chunk_text("short text", max_chars=2000) == ["short text"]


def _fake_client(content: str):
    client = MagicMock()
    client.chat.return_value = MagicMock(message=MagicMock(content=content))
    return client


def test_curate_chunk_parses_json_array():
    with patch("ingest.curate._client", return_value=_fake_client('["joke one", "joke two"]')):
        result = curate_chunk("raw text")

    assert result == ["joke one", "joke two"]


def test_curate_chunk_unwraps_object_with_list_value():
    with patch("ingest.curate._client", return_value=_fake_client('{"result": ["joke one"]}')):
        result = curate_chunk("raw text")

    assert result == ["joke one"]


def test_curate_chunk_returns_empty_on_bad_json():
    with patch("ingest.curate._client", return_value=_fake_client("not json at all")):
        result = curate_chunk("raw text")

    assert result == []


def test_curate_text_tags_each_extracted_joke():
    with patch("ingest.curate.chunk_text", return_value=["chunk1", "chunk2"]):
        with patch("ingest.curate.curate_chunk", side_effect=[["joke1"], ["joke2", "joke3"]]):
            entries = curate_text("source text", tags=["programmers"])

    assert [e.text for e in entries] == ["joke1", "joke2", "joke3"]
    assert all(e.tags == ["programmers"] for e in entries)
