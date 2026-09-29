from unittest.mock import patch

from store import VectorStore

VECTORS = {
    "developer entered the office": [1.0, 0.0],
    "about a programmer and a light bulb": [0.0, 1.0],
    "developer left the office": [0.9, 0.1],
}


def fake_embed(texts):
    return [VECTORS[t] for t in texts]


def test_add_and_search_returns_most_similar_first():
    store = VectorStore()
    with patch("store.embed", side_effect=fake_embed):
        store.add(list(VECTORS.keys()), tags=[["spy"], ["IT"], ["spy"]])
        results = store.search("developer entered the office", k=2)

    assert len(results) == 2
    assert results[0].entry.text == "developer entered the office"
    assert results[1].entry.text == "developer left the office"
    assert results[0].score > results[1].score


def test_search_on_empty_store_returns_empty_list():
    store = VectorStore()
    assert store.search("anything") == []


def test_filter_before_selecting_top_k():
    store = VectorStore()
    with patch("store.embed", side_effect=fake_embed):
        store.add(list(VECTORS))
        results = store.search(
            "developer entered the office", k=2,
            predicate=lambda entry: entry.text != "developer entered the office",
        )
    assert len(results) == 2
    assert results[0].entry.text == "developer left the office"


def test_save_and_load_roundtrip(tmp_path):
    store = VectorStore()
    with patch("store.embed", side_effect=fake_embed):
        store.add(list(VECTORS.keys()), tags=[["spy"], ["IT"], ["spy"]])
        store.save(str(tmp_path))

    loaded = VectorStore.load(str(tmp_path))
    assert len(loaded) == len(store)

    with patch("store.embed", side_effect=fake_embed):
        results = loaded.search("developer entered the office", k=1)
    assert results[0].entry.text == "developer entered the office"
    assert results[0].entry.tags == ["spy"]
