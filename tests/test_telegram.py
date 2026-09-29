import json
from unittest.mock import patch

from ingest.telegram import build, parse_export


def test_export_and_resumable_index(tmp_path, monkeypatch):
    path = tmp_path / "jokes.json"
    path.write_text(json.dumps({"name": "Humor", "messages": [
        {"type": "service", "text": "service"},
        {"type": "message", "text": "  short joke  "},
        {"type": "message", "text": "short joke"},
        {"type": "message", "text": ["Hello, ", {"type": "bold", "text": "world"}],
         "text_entities": [{"type": "hashtag", "text": "#humor"}]},
        {"type": "message", "text": ""},
    ]}), encoding="utf-8")
    entries = parse_export(str(path))
    assert [entry.text for entry in entries] == ["short joke", "Hello, world"]
    assert entries[1].tags == ["Humor", "#humor"]
    monkeypatch.setenv("JOKER_STORE_DIR", str(tmp_path / "store"))
    with patch("store.embed", return_value=[[1.0, 2.0]]) as embed:
        assert len(build(str(path), batch_size=1)) == 2
        assert embed.call_count == 2
    with patch("store.embed") as embed:
        assert len(build(str(path))) == 2
        embed.assert_not_called()
