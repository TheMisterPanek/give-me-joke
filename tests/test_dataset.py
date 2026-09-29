from unittest.mock import patch

import pytest

from ingest.dataset import Record, build, read_records
from reactions import load_scores, text_key


def test_custom_file_parser_and_telegram_contract(tmp_path):
    import json

    source = tmp_path / "demo.csv"
    source.write_text('body,category,likes\n"Synthetic text for a test.",test,7\n', encoding="utf-8")
    records = list(read_records(str(source), "examples/csv_parser.py:parse"))
    assert len(records) == 1
    assert records[0].reactions == 7
    assert records[0].tags == ["test"]
    source = tmp_path / "export.json"
    source.write_text(json.dumps({"name": "test", "messages": [
        {"type": "message", "text": "Synthetic text for a test."}
    ]}), encoding="utf-8")
    assert len(list(read_records(str(source)))) == 1


@pytest.mark.parametrize("row", ['{"text": ""}', '{"text": "ok", "reactions": -1}',
                                 '{"text": "ok", "tags": "tag"}', '{"text": 10}'])
def test_invalid_rows_identify_the_record(tmp_path, row):
    source = tmp_path / "bad.jsonl"
    source.write_text(row, encoding="utf-8")
    with pytest.raises(ValueError, match="Record 1"):
        list(read_records(str(source), "jsonl"))


def test_resume_and_duplicate_reactions_without_reembedding(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKER_STORE_DIR", str(tmp_path / "store"))
    rows = [Record(text="joke", reactions=2), Record(text="joke", reactions=8)]
    with patch("store.embed", return_value=[[1.0, 2.0]]) as embed:
        assert len(build(rows, batch_size=1)) == 1
        embed.assert_called_once()
    assert load_scores()[text_key("joke")] == 8
    with patch("store.embed") as embed:
        assert len(build([Record(text="joke", reactions=12)])) == 1
        embed.assert_not_called()
    assert load_scores()[text_key("joke")] == 12
