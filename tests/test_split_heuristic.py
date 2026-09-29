from ingest.split_heuristic import is_probably_joke, split_jokes


def test_split_jokes_groups_sentences_up_to_target_len():
    text = "The first sentence is fairly long. The second sentence is also long. Here is another long sentence."
    jokes = split_jokes(text, target_len=20)

    assert len(jokes) >= 2
    assert " ".join(jokes) == text


def test_split_jokes_empty_text_returns_empty_list():
    assert split_jokes("") == []


def test_is_probably_joke_filters_by_length():
    assert not is_probably_joke("short")
    assert is_probably_joke("a" * 100)
    assert not is_probably_joke("a" * 900)
