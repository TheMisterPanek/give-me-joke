from ingest.text_book import parse_book

BOOK = """Thank you for downloading the book...

T A B L E  O F  C O N T E N T S

ABOUT THE FIRST CHARACTER

ABOUT THE SECOND CHARACTER

????????
?TITLE?
????????

This table of contents will be discarded.

????????
?ABOUT THE FIRST CHARACTER?
????????

The first character started a check. Continued, but the file
was not found.

The first character completed the check and saved the result.

?????????????
?ABOUT THE SECOND CHARACTER?
?????????????

The second character asks a colleague about the news.
"""


def test_parse_book_skips_toc_and_extracts_sections(tmp_path):
    path = tmp_path / "book.txt"
    path.write_text(BOOK, encoding="utf-8")

    sections = parse_book(str(path), encoding="utf-8")

    assert [s.title for s in sections] == ["ABOUT THE FIRST CHARACTER", "ABOUT THE SECOND CHARACTER"]
    assert sections[0].text == (
        "The first character started a check. Continued, but the file was not found. "
        "The first character completed the check and saved the result."
    )
    assert sections[1].text == "The second character asks a colleague about the news."
