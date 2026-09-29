import json

from reactions import build_scores, load_scores, text_key


def test_scores_match_formatted_text_and_use_maximum_for_duplicates(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKER_STORE_DIR", str(tmp_path / "store"))
    source = tmp_path / "export.json"
    source.write_text(json.dumps({"messages": [
        {"type": "message", "text": [" jo", {"text": "ke "}],
         "reactions": [{"emoji": "🤡", "count": 10}, {"emoji": "❤", "count": 5},
                       {"emoji": "💩", "count": 100}]},
        {"type": "message", "text": "joke", "reactions": [{"emoji": "👍", "count": 3}]},
        {"type": "message", "text": "other"},
        {"type": "service", "text": "service"},
    ]}), encoding="utf-8")
    scores = build_scores(str(source))
    assert scores == {text_key("joke"): 15, text_key("other"): 0}
    assert load_scores() == scores
