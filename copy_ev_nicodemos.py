import re
from rich import print
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import typing as t
import json


OUTPUT_DIR = Path("./json/apocrifos/pt-br/evangelho-nicodemos/")

class OutputMeta(t.TypedDict):
    title: str
    abbrev: str

class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]


VERSIONS = ['grega-e-latina', 'grega', 'latina']

def _get_version(title: str) -> str:
    if title == "(Versão Grega e Latina)":
        return "grega-e-latina"
    if title == "(Versão Grega)":
        return "grega"
    if title == "(Versão Latina)":
        return "latina"
    raise ValueError(f"Unknown version: {title}")

GET_BOOK = "https://verdadeperdida.wordpress.com/2013/03/03/evangelho-de-nicodemus-descida-de-jesus-ao-inferno/"

META: t.Final = OutputMeta(
    title="Evangelho de Nicodemos",
    abbrev="evangelho-nicodemos",
)

def compact_json(raw) -> str:
    return json.dumps(raw, separators=(',', ':')).replace("\n", "")


def _pull_chapters() -> t.Generator[tuple[dict[str, str], int, str], None, None]:
    resp = requests.get(GET_BOOK)
    resp.raise_for_status()
    raw_html = resp.text

    soup = BeautifulSoup(raw_html, 'html.parser')
    verses: dict[str, str] = {}

    main_content = soup.find('div', id='main-content')
    article = main_content.find("div", class_="clearfix")
    all_p = list(article.find_all(['p']))

    cur_ch = None
    cur_version = None

    for p in all_p:
        text: str = p.get_text(strip=True)

        if "(Versão" in text:
            if cur_version and cur_ch:
                yield verses, cur_ch, cur_version
                verses = {}

            cur_ch = None
            cur_version = _get_version(text)
            continue

        if text.startswith("Capítulo"):
            if cur_ch:
                yield verses, cur_ch, cur_version
                verses = {}

            cur_ch = int(text.split(" ")[1])
            continue

        if cur_ch:
            verse_num, *verse_content = text.split(" ", maxsplit=1)

            if not verse_num.isdigit():
                verse_num = 1
                verse_content = text

            verses[verse_num] = verse_content
            continue

    yield verses, cur_ch, cur_version


def main() -> None:
    for chapter_content, ch, version in _pull_chapters():
        output_file = OUTPUT_DIR / version / f"{ch}.json"

        new_content = Output(
            meta=META,
            chapter=ch,
            content=chapter_content
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(compact_json(new_content))

        print(f"Write [green]{output_file}[/green]")



if __name__ == "__main__":
    main()
