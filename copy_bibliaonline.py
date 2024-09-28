from time import sleep
from rich import print
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import typing as t
import json


OUTPUT_DIR = Path("./json/pt-br/")

class OutputMeta(t.TypedDict):
    title: str
    abbrev: str

class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]

LIST_BOOKS = "https://www.abibliadigital.com.br/api/books"
GET_CHAPTER = "https://www.bibliaonline.com.br/{VERSION}/{ABBREV}/{CHAPTER}"
VERSIONS = ["ara", "acf", "nvi"]

def compact_json(raw) -> str:
    return json.dumps(raw, separators=(',', ':')).replace("\n", "")

def _pull_chapter(version: str, abbrev: str, chapter: int) -> tuple[dict[str, str], dict[str, str]]:
    resp = requests.get(GET_CHAPTER.format(VERSION=version, ABBREV=abbrev, CHAPTER=chapter))
    resp.raise_for_status()
    raw_html = resp.text

    soup = BeautifulSoup(raw_html, 'html.parser')
    verses: dict[str, str] = {}
    titles: dict[str, str] = {}

    for div_tag in soup.find_all("div", class_="l0", attrs={'data-v': True}):
        title_span = div_tag.find("span", class_="t")
        title_idx = title_span["data-v"].lstrip(".").rstrip(".")
        title_text = title_span.get_text(strip=True)
        titles[title_idx] = title_text

    for p_tag in soup.find_all('p', class_='l0', attrs={'data-v': True}):
        for verse_number_span in p_tag.find_all('span', class_='v', attrs={'data-v': True}):
            verse_text = None
            verse_number = None

            # Extract the verse number from the <span class="v"> tag
            verse_number = verse_number_span.get_text(strip=True)

            # Extract the verse text from the <span class="t"> tag
            verse_text_tag = verse_number_span.find_next("span", class_="t")
            if verse_text_tag:
                verse_text = verse_text_tag.get_text(strip=True)

            if verse_number and verse_text:
                verses[str(verse_number)] = verse_text

    return verses, titles

def _download_version(meta: OutputMeta, version: str, abbrev: str, chapters: int):
    try:
        for ch in range(1, chapters +1):
            output_file = OUTPUT_DIR / version / abbrev / f"{ch}.json"
            if output_file.exists():
                continue

            for attempt in range(3):
              try:
                chapter_content, title_content = _pull_chapter(version, abbrev, ch)
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

            if title_content:
                new_content["titles"] = title_content

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(compact_json(new_content))

            print(f"Write [green]{output_file}[/green]")
    except Exception:
        print(f"Error on [red]{meta['title']}[/red]")
        raise

def main():
    resp = requests.get(LIST_BOOKS).json()
    for book in resp:
        abbrev = book["abbrev"]["pt"]
        title = book["name"]
        chapters = book["chapters"]

        if abbrev == "job":
            abbrev = "jó"

        meta = OutputMeta(
            title=title,
            abbrev=abbrev,
        )

        for version in VERSIONS:
            _download_version(meta, version, abbrev, chapters)


if __name__ == "__main__":
    main()
