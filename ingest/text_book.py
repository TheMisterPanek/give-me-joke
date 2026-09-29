import re
from dataclasses import dataclass

_BORDER_RE = re.compile(r"^\?+$")


@dataclass
class Section:
    title: str
    text: str


def parse_book(path: str, encoding: str = "cp1251") -> list[Section]:
    """Parse a sectioned text book: sections are framed by
    a border line of '?' characters, then the section title, then a
    border line again, then the section's raw text.

    Blank lines in this format are just print spacing (every line is
    followed by one), not paragraph breaks, so they carry no meaning
    and are collapsed away. Splitting the section text into individual
    jokes is left to the LLM curation step, which also has to judge
    what's junk.
    """
    with open(path, encoding=encoding) as f:
        lines = f.read().splitlines()

    border_indices = [i for i, line in enumerate(lines) if _BORDER_RE.match(line.strip())]

    sections: list[Section] = []
    i = 0
    while i + 1 < len(border_indices):
        title_start = border_indices[i] + 1
        title_end = border_indices[i + 1]
        title = " ".join(l.strip() for l in lines[title_start:title_end] if l.strip())
        title = title.strip("? ")

        body_start = title_end + 1
        body_end = border_indices[i + 2] if i + 2 < len(border_indices) else len(lines)
        text = " ".join(l.strip() for l in lines[body_start:body_end] if l.strip())

        if title and text:
            sections.append(Section(title=title, text=text))
        i += 2

    # The first bordered block is the book's own title/table-of-contents,
    # not a joke section - drop it.
    return sections[1:]
