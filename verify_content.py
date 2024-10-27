# Write a script that will read all files under json/pt-br/ and ensure that all:
# 1. All books exists in all versions
# 2. All books have the same number of chapters
# 3. Every chapter have the same number of verses


from collections import defaultdict
from pathlib import Path
import json
from rich.console import Console
from rich.table import Table
from rich import box
from rich.style import Style
import typing as t

class OutputMeta(t.TypedDict):
    title: str
    abbrev: str

class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]

class ReadResult(t.TypedDict):
    version: str
    book: str
    chapter: str
    content: dict[str, str]

def read_json_files(directory: Path) -> t.Generator[ReadResult, None, None]:
    json_files = directory.glob('**/*.json')
    for file in json_files:
        with file.open('r', encoding='utf-8') as f:
            version = file.parent.parent.name
            book = file.parent.name
            chapter = file.stem
            yield {
                "version": version,
                "book": book,
                "chapter": chapter,
                "content": json.load(f)
            }

VERSION_KEY = str
BOOK_KEY = str
CHAPTER_KEY = int
VERSE_COUNT = int

def get_book_chapter_verse_counts(directory: Path) -> dict[str, dict[str, t.Tuple[int, int]]]:
    counts = {}
    outputs = read_json_files(directory)
    counts: dict[VERSION_KEY, dict[BOOK_KEY, dict[CHAPTER_KEY, VERSE_COUNT]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for output in outputs:
        version = output["version"].upper()
        book = output["book"]
        chapter = int(output["chapter"])
        verse_count = len(output["content"]["content"])

        counts[version][book][chapter] = verse_count

    return counts

def create_table(counts):
    console = Console()
    table = Table(box=box.SIMPLE)

    # Add columns for each version
    versions = list(counts.keys())
    table.add_column("Book + Chapter")
    for version in versions:
        table.add_column(version, justify="right")

    # Iterate through books and chapters to populate rows
    books = set()
    for version_counts in counts.values():
        books.update(version_counts.keys())

    for book in sorted(books):
        chapters_set = set()
        for version in versions:
            if book in counts[version]:
                chapters_set.update(counts[version][book].keys())

        for chapter in sorted(chapters_set):
            row = [f"{book} {chapter}"]

            for version in versions:
                first_col_verse_count = counts[versions[0]][book].get(chapter)

                if book in counts[version] and chapter in counts[version][book]:
                    verse_count = counts[version][book][chapter]
                    if verse_count != first_col_verse_count:
                        row.append(f"[red]{verse_count} verses[/red]")
                    else:
                        row.append(f"{verse_count} verses")
                else:
                    row.append("N/A")

            table.add_row(*row)

        # input("")

    console.print(table)

def main():
    directory = Path('json/pt-br/')
    counts = get_book_chapter_verse_counts(directory)
    create_table(counts)

if __name__ == "__main__":
    main()
