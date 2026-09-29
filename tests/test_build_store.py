from unittest.mock import patch

from ingest.build_store import build
from ingest.text_book import Section


def fake_embed(texts):
    return [[float(hash(t) % 1000), 1.0] for t in texts]


def test_build_skips_already_stored_jokes(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKER_STORE_DIR", str(tmp_path / "store"))

    sections = [Section(title="section", text="some raw text")]

    with patch("ingest.build_store.parse_book", return_value=sections):
        with patch(
            "ingest.build_store.split_jokes", return_value=["joke one " * 5, "joke two " * 5]
        ):
            with patch("store.embed", side_effect=fake_embed):
                store = build(book_path="ignored.txt")

    assert len(store) == 2

    # Second run: same section -> jokes already in store -> nothing new added.
    with patch("ingest.build_store.parse_book", return_value=sections):
        with patch(
            "ingest.build_store.split_jokes", return_value=["joke one " * 5, "joke two " * 5]
        ):
            with patch("store.embed", side_effect=fake_embed) as mock_embed:
                store2 = build(book_path="ignored.txt")

    assert len(store2) == 2
    mock_embed.assert_not_called()
