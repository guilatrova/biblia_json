from time import sleep
from rich import print
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import typing as t
import json
import unicodedata



class OutputMeta(t.TypedDict):
    title: str
    abbrev: str

class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]

VERSION_OUTPUT_DIR = Path("./json/pt-br/bkjf/")
LIST_BOOKS = "https://www.abibliadigital.com.br/api/books"
GET_CHAPTER = "http://bkjfiel.com.br/{BOOK}-{CHAPTER}"

def compact_json(raw) -> str:
    return json.dumps(raw, separators=(',', ':')).replace("\n", "")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
}

def _pull_chapter(book: str, chapter: int) -> dict[str, str]:
    resp = requests.get(GET_CHAPTER.format(BOOK=book, CHAPTER=chapter), headers=headers)
    resp.raise_for_status()
    raw_html = resp.text

    soup = BeautifulSoup(raw_html, 'html.parser')
    verses: dict[str, str] = {}

    p_tags = soup.find_all('p', class_='pb-6 xl:pb-8')
    for p in p_tags:
        a_tag = p.find('a', class_='btn-link')
        if a_tag and 'title' in a_tag.attrs:
            title = a_tag['title']
            _, chapter_verse = title.rsplit(' ', 1)
            _, verse_num = chapter_verse.split(':')
            verse_text = a_tag.get_text(strip=True)
            if verse_text.startswith(verse_num):
                verse_text = verse_text[len(verse_num):].strip()

            verses[verse_num] = verse_text

    return verses

def _download_book(meta: OutputMeta, book: str, abbrev: str, chapters: int) -> None:
    try:
        for ch in range(1, chapters +1):
            output_file = VERSION_OUTPUT_DIR / abbrev / f"{ch}.json"
            if output_file.exists():
                continue

            for attempt in range(3):
              try:
                chapter_content = _pull_chapter(book, ch)
                break
              except Exception as e:
                print(f"[red]Attempt {attempt + 1} failed:[/red] {e}")
                if attempt < 2:
                  print("[yellow]Retrying in 10 seconds...[/yellow]")
                  sleep(10)
                else:
                  raise

            new_content = Output(
                meta=meta,
                chapter=ch,
                content=chapter_content
            )

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(compact_json(new_content))

            print(f"Write [green]{output_file}[/green]")
    except Exception:
        print(f"Error on [red]{meta['abbrev']}[/red]")
        raise


def remove_accents(input_str: str) -> str:
    normalized_str = unicodedata.normalize('NFD', input_str)
    return ''.join(c for c in normalized_str if unicodedata.category(c) != 'Mn')

def main():
    resp = requests.get(LIST_BOOKS).json()
    for book in resp:
        abbrev = book["abbrev"]["pt"]
        title = book["name"]
        chapters = book["chapters"]

        if abbrev == "job":
            abbrev = "jo"


        meta = OutputMeta(
            title=title,
            abbrev=abbrev,
        )

        book = remove_accents(title.lower())
        match abbrev:
            case "ct":
                book = "cantares-de-salomao"

            case "lm":
                book = "lamentacoes"

            case "at":
                book = "atos-dos-apostolos"

            case _ if abbrev.startswith("1") or abbrev.startswith("2") or abbrev.startswith("3"):
                book = book.replace("ª ", "-").replace("º ", "-")

        _download_book(meta, book, abbrev, chapters)


if __name__ == "__main__":
    main()
