# Experiment: semantic joke retrieval

This project retrieves existing texts rather than generating jokes. It uses
`qwen3-embedding:0.6b`, normalized float32 vectors, and cosine similarity.

The local experiment indexed 24,563 records: 4,592 from an earlier text source
and 19,971 unique texts from a Telegram export. Each Telegram post becomes one
record; texts are not split into sentences. Formatting fragments are joined,
and empty/service messages and exact duplicates are skipped. Neither the source
datasets nor the resulting index are published.

## Findings

The first version randomly selected one of the five nearest results. Short
queries often returned single-word image captions. Semantic similarity alone
does not tell us whether a text is a complete joke. We added a retrieval-time
filter without recomputing the embeddings.

Current algorithm:

1. Exclude texts shorter than 40 characters or seven words, without `. ! ? …`
   or a line break, containing `@`, HTTP links, `t.me/`, or subscription/advertising
   markers. Both English and Russian advertising markers are supported.
2. Retrieve the 15 nearest eligible texts by meaning.
3. Keep the five with the highest positive-reaction counts.
4. Return one of these five uniformly at random.

🤡, ❤/❤️, 👍, 😁, 😂, 🤣, 🔥, and 🥰 all have equal weight. Duplicate posts of the
same text use the maximum score, not the sum. Semantic similarity breaks ties;
missing scores count as zero. Scores are stored separately from vectors and
can be updated without reindexing.

## Limitations and evaluation status

This is a heuristic prototype without a labeled benchmark or quantitative
quality evaluation. The filter can reject a good short joke or admit a long
non-joke. By design, `@` excludes even non-advertising texts. There is no minimum
similarity threshold, so the service may return a merely relative match.

Reaction counts depend on the audience, post age, and views; they are not an
objective humor score and are not normalized by views. Treating 🤡 as positive
is a choice in this experiment, not a universal interpretation. Unrated sources
with a score of zero may lose to Telegram posts.

For a reproducible test without private data, `tools/make_demo.py` generates a
tiny synthetic example with invented reactions under gitignored `data/`. Real
exports, channel names, and source collection names are not published.
