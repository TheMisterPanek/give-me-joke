import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bot import respond, split_reply
from retrieval import choose_joke, is_joke_candidate
from store import Entry, SearchResult
from reactions import text_key


def test_choose_from_top_five():
    results = [SearchResult(Entry(str(i)), 1.0) for i in range(5)]
    store = Mock()
    store.search.return_value = results
    with patch("retrieval.random.choice", return_value=results[4]) as choice:
        assert choose_joke(store, "about this topic") == "4"
    store.search.assert_called_once_with("about this topic", k=15, predicate=is_joke_candidate)
    choice.assert_called_once_with(results)


def test_choose_top_five_by_reactions_within_semantic_fifteen():
    results = [SearchResult(Entry(str(i)), 1 - i / 20) for i in range(15)]
    store = Mock()
    store.search.return_value = results
    scores = {text_key(str(i)): i for i in range(15)}
    with patch("retrieval.random.choice", side_effect=lambda values: values[0]) as choice:
        assert choose_joke(store, "any topic", scores) == "14"
    assert [r.entry.text for r in choice.call_args.args[0]] == ["14", "13", "12", "11", "10"]


def test_filter_captions_and_keep_short_joke():
    for text in ["Singleword", "caption", "Name", "#hashtag",
                 "Visit our channel @some_channel for lots of funny jokes!",
                 "Subscribe to our channel for lots of great jokes!"]:
        assert not is_joke_candidate(Entry(text))
    assert is_joke_candidate(Entry("A developer updated the kettle. Now you must accept the terms before boiling."))


def test_long_reply_preserves_text_and_telegram_limit():
    text = "😀joke\n" * 1500
    chunks = split_reply(text)
    assert "".join(chunks) == text
    assert all(len(chunk.encode("utf-16-le")) // 2 <= 4000 for chunk in chunks)


def test_search_failure_replies_without_crashing():
    message = SimpleNamespace(text="topic", reply_text=AsyncMock())
    update = SimpleNamespace(effective_message=message)
    context = SimpleNamespace(bot_data={"store": Mock()})
    with patch("bot.choose_joke", side_effect=RuntimeError("offline")):
        asyncio.run(respond(update, context))
    message.reply_text.assert_awaited_once_with("Search is temporarily unavailable. Please try again later.")
