import re
from rich import print
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import typing as t
import json


OUTPUT_DIR = Path("./json/apocrifos/pt-br/pastor-hermas/")

class OutputMeta(t.TypedDict):
    title: str
    abbrev: str

class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]

GET_BOOK = "https://web.archive.org/web/20220519114256/http://www.e-cristianismo.com.br/historia-do-cristianismo/pais-apostolicos/o-pastor-de-hermas.html"

META: t.Final = OutputMeta(
    title="Pastor de Hermas",
    abbrev="pastor-hermas",
)

def compact_json(raw) -> str:
    return json.dumps(raw, separators=(',', ':')).replace("\n", "")

def _break_long_str(raw: str) -> dict[str, str]:
    """Divide uma string longa em parágrafos, numerando-os como '1', '2', etc."""

    # Quebra o texto com base em finalizações de sentença e pontuações seguidas por um espaço.
    # Inclui ponto final, interrogação, exclamação e vírgula (para sentenças curtas que devem ser concatenadas).
    sentences = re.split(r'(?<=[\.\?!])\s+(?=[A-Z])', raw)

    # Concatenar sentenças muito curtas (menores de 30 caracteres) com a próxima, se possível.
    paragraphs = []
    buffer = ""
    for sentence in sentences:
        if len(sentence) < 30 and buffer:
            buffer += " " + sentence
        else:
            if buffer:
                paragraphs.append(buffer.strip())
            buffer = sentence
    if buffer:
        paragraphs.append(buffer.strip())

    # Gerar o dicionário numerado.
    return {str(i + 1): para for i, para in enumerate(paragraphs)}

def _pull_chapters() -> t.Generator[tuple[dict[str, str], dict[str, str]], None, None]:
    resp = requests.get(GET_BOOK)
    resp.raise_for_status()
    raw_html = resp.text

    soup = BeautifulSoup(raw_html, 'html.parser')
    verses: dict[str, str] = {}
    titles: dict[str, str] = {}
    cur_ch = 0

    content_div = soup.find('div', class_='itemFullText')

    for child in content_div.find_all(['h3', 'h4', 'p']):
        match child.name:
            case 'h3':
                titles["1"] = child.get_text(strip=True)

            case 'h4':
                if cur_ch > 0:
                    yield verses, titles
                    verses = {}
                    titles = {}

                cur_ch += 1

            case 'p':
                full_chapter_content = child.get_text(strip=True)
                verses = _break_long_str(full_chapter_content)


def main() -> None:
    ch = 1
    for chapter_content, title_content in _pull_chapters():
        output_file = OUTPUT_DIR / f"{ch}.json"

        new_content = Output(
            meta=META,
            chapter=ch,
            content=chapter_content
        )

        if title_content:
            new_content["titles"] = title_content

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(compact_json(new_content))

        print(f"Write [green]{output_file}[/green]")

        ch += 1


if __name__ == "__main__":
    main()
