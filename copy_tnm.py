import re
from time import sleep
from rich import print
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import typing as t
import json
import threading


BR_OUTPUT_DIR = Path("./json/pt-br/")
US_OUTPUT_DIR = Path("./json/en-us/")

class OutputMeta(t.TypedDict):
    title: str
    abbrev: str

class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]

LIST_BOOKS = "https://www.abibliadigital.com.br/api/books"
GET_BR_CHAPTER = "https://www.jw.org/pt/biblioteca/biblia/biblia-de-estudo/livros/{BOOK}/{CHAPTER}/"
GET_US_CHAPTER = "https://www.jw.org/en/library/bible/study-bible/books/{BOOK}/{CHAPTER}/"
# https://www.jw.org/en/library/bible/study-bible/books/john/8/
BR_VERSIONS = ["tnm"]
US_VERSIONS = [] # tnw

def compact_json(raw) -> str:
    return json.dumps(raw, separators=(',', ':')).replace("\n", "")

def _trim_verse_txt(raw: str, cur_verse: str) -> str:
    raw = raw.lstrip(cur_verse).replace("*", "").replace("+", "").replace("  ", " ").strip()
    return re.sub(r'\s+', ' ', raw)

def _pull_chapter(book: str, chapter: int) -> dict[str, str]:
    resp = requests.get(GET_BR_CHAPTER.format(BOOK=book, CHAPTER=chapter))
    resp.raise_for_status()
    raw_html = resp.text

    soup = BeautifulSoup(raw_html, 'html.parser')
    verses: dict[str, str] = {}

    bible_text_div = soup.find("div", {"id": "bibleText"})

    for verse_span in bible_text_div.find_all("span", class_="verse"):
        if not verses:
            verse_num = "1"
            # João 8 na TNM começa em 12
            if chapter == 8 and book == "João":
                verse_num = "8 12"
        else:
            verse_num = verse_span.find("sup", class_="verseNum").text.strip()
        verse_text = verse_span.get_text(separator=" ", strip=True)
        verses[verse_num] = _trim_verse_txt(verse_text, verse_num)


    if not verses:
        raise Exception(f"No verses found for {book} {chapter}")

    return verses

def _download_version(meta: OutputMeta, version: str, book: str, abbrev: str, chapters: int, output_dir: Path) -> None:
    try:
        for ch in range(1, chapters +1):
            output_abbrev = "at" if abbrev == "atos" else abbrev
            output_file = output_dir / version / output_abbrev / f"{ch}.json"
            if output_file.exists():
                continue

            for attempt in range(3):
              try:
                chapter_content = _pull_chapter(book, ch)
                break
              except Exception as e:
                print(f"[red]Attempt {attempt + 1} failed:[/red] {e}")
                if attempt < 2:
                  print("[yellow]Retrying in 60 seconds...[/yellow]")
                  sleep(60)
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
        print(f"Error on [red]{meta['title']}[/red]")
        raise

def main():
    book_data = json.loads(Path("json/books.json").read_text())
    threads = []

    def process_book(book):
        abbrev = book["abbrev"]["pt"]
        title = book["name"]
        chapters = book["chapters"]

        title = title.replace("º ", "-").replace("ª ", "-")

        if abbrev == "job":
            abbrev = "jó"
        elif abbrev == "at":
            abbrev = "atos"

        meta = OutputMeta(
            title=title.replace("-", " "),
            abbrev="at" if abbrev == "atos" else abbrev,
        )

        if abbrev == "lm":
            title = "Lamentações"
        elif abbrev == "ct":
            title = "Cântico-de-Salomão"
        elif abbrev == "fm":
            title = "Filêmon"

        for version in BR_VERSIONS:
            _download_version(meta, version, title, abbrev, chapters, BR_OUTPUT_DIR)

        for version in US_VERSIONS:
            _download_version(meta, version, title, abbrev, chapters, US_OUTPUT_DIR)

    semaphore = threading.Semaphore(5)

    def thread_function(book):
        with semaphore:
            process_book(book)

    for book in book_data:
        thread = threading.Thread(target=thread_function, args=(book,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
