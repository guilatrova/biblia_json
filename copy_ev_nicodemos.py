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

def _fix_grego_latino_prologue(content: Output) -> Output:
    content["content"]["0"] = "\n".join(
        [
            "Eu, ANANIAS, protetor, de hierarquia pretoriana, perito em leis, vim através das divinas Escrituras tomar conhecimento de Nosso Senhor Jesus Cristo e me aproximei dele pela fé, e permiti-me receber o santo batismo; agora sinto-me bem, depois de seguir “a pista das narrações relativas a Nosso Senhor Jesus Cristo, que foram feitas naquela época, e que os judeus deixaram guardadas com Pôncio Pilatos; encontrei-as como estavam, escritas em hebraico, e com o beneplácito divino traduzi-as para o grego, para conhecimento de todos os que invocam o nome de Nosso Senhor Jesus Cristo, durante o reinado de Flávio Teodósio, nosso senhor, no ano 17, e sexto de Flávio Valentino, na nona indicação.",
            "Todos, pois, quantos leiam e traduzam isto para outros livros, lembrem-se e peçam por mim para que o Senhor seja piedoso para comigo e me perdoe os pecados que cometi contra ele.",
            "Paz aos leitores, aos ouvintes e aos seus servidores. Amém.",
            "No ano décimo quinto do governo de Tibério César, imperador dos romanos; no ano décimo nono do governo de Herodes, rei da Galiléia; no oitavo dia das calendas de abril, correspondente ao dia 25 de março; durante o consulado de Rufo e Rubelião; no quarto ano da olimpíada 202; sendo, nessa época, José Caifás o sumo sacerdote dos judeus. Tudo o que Nicodemus narrou com base no tormento da cruz e da paixão do Senhor, transmitiu-o aos príncipes dos sacerdotes e aos demais judeus depois de havê-lo redigido ele mesmo em hebraico.",
        ]
    )

    content["titles"] = {
        "0": "Prólogo",
        "1": "Narrações Sobre Nosso Senhor Jesus Cristo Compostas no Tempo de Pôncio Pilatos",
    }

    return content


def main() -> None:
    for chapter_content, ch, version in _pull_chapters():
        output_file = OUTPUT_DIR / version / f"{ch}.json"

        new_content = Output(
            meta=META,
            chapter=ch,
            content=chapter_content
        )

        if version == "grega-e-latina" and ch == 1:
            new_content = _fix_grego_latino_prologue(new_content)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(compact_json(new_content))

        print(f"Write [green]{output_file}[/green]")



if __name__ == "__main__":
    main()