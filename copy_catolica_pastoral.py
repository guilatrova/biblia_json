from time import sleep
from rich import print
from pathlib import Path
import typing as t
import json
from bs4 import BeautifulSoup
import requests


class OutputMeta(t.TypedDict):
    title: str
    abbrev: str


class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]


GET_CHAPTER = (
    "https://biblia.paulus.com.br/api/v1/chapters?book={BOOK}&chapter={CHAPTER}"
)
VERSION: t.Final = "biblia-pastoral"
BR_OUTPUT_DIR: t.Final = Path("./json/catolicos/pt-br/") / VERSION
AT: t.Final = "antigo-testamento"
NT: t.Final = "novo-testamento"


def build_payload(at: bool, book: str, chapter: int) -> dict[str, str]:
    slug = "antigo-testamento" if at else "novo-testamento"
    return {
        "new_testament_slug": slug,
        "book_slug": book,
        "chapter_order": chapter,
    }


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
}


def compact_json(raw) -> str:
    return json.dumps(raw, separators=(",", ":")).replace("\n", "")


class Versicle(t.TypedDict):
    value: str
    text: str


class ChapterRespData(t.TypedDict):
    versicles: list[Versicle]


def _trim_html_as_text(html: str) -> str:
    html = html.strip()
    soup = BeautifulSoup(html, "html.parser")
    result = soup.get_text(separator=" ", strip=True)

    return result


def _pull_chapter(book: str, chapter: int) -> dict[str, str]:
    response = requests.get(
        GET_CHAPTER.format(BOOK=book, CHAPTER=chapter), headers=headers
    )
    response.raise_for_status()
    resp = response.json()

    data: list[ChapterRespData] = resp["data"][0]

    verses: dict[str, str] = {}

    for item in data["versicles"]:
        verse = item["value"]
        content = item["text"]

        verses[str(verse)] = _trim_html_as_text(content)

    return verses


def _download_version(
    meta: OutputMeta, abbrev: str, book: str, chapters: int, output_dir: Path
):
    try:
        for ch in range(1, chapters + 1):
            output_file = output_dir / abbrev / f"{ch}.json"
            if output_file.exists():
                continue

            for attempt in range(3):
                try:
                    chapter_content = _pull_chapter(book, ch)
                    if len(chapter_content) == 0:
                        print(f"[red]Empty chapter {abbrev} {ch}[/red]")
                        continue
                    break
                except Exception as e:
                    print(f"[red]Attempt {attempt + 1} failed:[/red] {e}")
                    if attempt < 2:
                        print("[yellow]Retrying in 1 seconds...[/yellow]")
                        sleep(1)
                    else:
                        raise

            new_content = Output(meta=meta, chapter=ch, content=chapter_content)

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(compact_json(new_content))

            print(f"Write [green]{output_file}[/green]")
    except Exception:
        print(f"Error on [red]{meta['title']}[/red]")
        raise


class BookRef(t.TypedDict):
    name: str
    abbrev: str
    chapters: int


BOOKS: list[BookRef] = [
    {"name": "Gênesis", "abbrev": "genesis", "chapters": 50},
    {"name": "Êxodo", "abbrev": "exodo", "chapters": 40},
    {"name": "Levítico", "abbrev": "levitico", "chapters": 27},
    {"name": "Números", "abbrev": "numeros", "chapters": 36},
    {"name": "Deuteronômio", "abbrev": "deuteronomio", "chapters": 34},
    {"name": "Josué", "abbrev": "livro-de-josue", "chapters": 24},
    {"name": "Juízes", "abbrev": "livro-dos-juizes", "chapters": 21},
    {"name": "Rute", "abbrev": "rute", "chapters": 4},
    {"name": "1 Samuel", "abbrev": "primeiro-livro-de-samuel", "chapters": 31},
    {"name": "2 Samuel", "abbrev": "segundo-livro-de-samuel", "chapters": 24},
    {"name": "1 Reis", "abbrev": "primeiro-livro-dos-reis", "chapters": 22},
    {"name": "2 Reis", "abbrev": "segundo-livro-dos-reis", "chapters": 25},
    {"name": "1 Crônicas", "abbrev": "primeiro-livro-das-cronicas", "chapters": 29},
    {"name": "2 Crônicas", "abbrev": "segundo-livro-das-cronicas", "chapters": 36},
    {"name": "Esdras", "abbrev": "esdras", "chapters": 10},
    {"name": "Neemias", "abbrev": "neemias", "chapters": 13},
    {"name": "Tobias", "abbrev": "tobias", "chapters": 14},
    {"name": "Judite", "abbrev": "judite", "chapters": 16},
    {"name": "Ester", "abbrev": "ester", "chapters": 10},
    {"name": "1 Macabeus", "abbrev": "primeiro-livro-dos-macabeus", "chapters": 16},
    {"name": "2 Macabeus", "abbrev": "segundo-livro-dos-macabeus", "chapters": 15},
    {"name": "Jó", "abbrev": "jo", "chapters": 42},
    {"name": "Salmos", "abbrev": "salmos", "chapters": 150},
    {"name": "Provérbios", "abbrev": "proverbios", "chapters": 31},
    {"name": "Eclesiastes", "abbrev": "eclesiastes", "chapters": 12},
    {"name": "Cântico dos Cânticos", "abbrev": "cantico-dos-canticos", "chapters": 8},
    {"name": "Sabedoria", "abbrev": "sabedoria", "chapters": 19},
    {"name": "Eclesiástico", "abbrev": "eclesiastico", "chapters": 51},
    {"name": "Isaías", "abbrev": "isaias", "chapters": 66},
    {"name": "Jeremias", "abbrev": "jeremias", "chapters": 52},
    {"name": "Lamentações", "abbrev": "lamentacoes", "chapters": 5},
    {"name": "Baruc", "abbrev": "baruc", "chapters": 6},
    {"name": "Ezequiel", "abbrev": "ezequiel", "chapters": 48},
    {"name": "Daniel", "abbrev": "daniel", "chapters": 14},
    {"name": "Oseias", "abbrev": "oseias", "chapters": 14},
    {"name": "Joel", "abbrev": "joel", "chapters": 4},
    {"name": "Amós", "abbrev": "amos", "chapters": 9},
    {"name": "Obadias", "abbrev": "abdias", "chapters": 1},
    {"name": "Jonas", "abbrev": "jonas", "chapters": 4},
    {"name": "Miquéias", "abbrev": "miqueias", "chapters": 7},
    {"name": "Naum", "abbrev": "naum", "chapters": 3},
    {"name": "Habacuque", "abbrev": "habacuc", "chapters": 3},
    {"name": "Sofonias", "abbrev": "sofonias", "chapters": 3},
    {"name": "Ageu", "abbrev": "ageu", "chapters": 2},
    {"name": "Zacarias", "abbrev": "zacarias", "chapters": 14},
    {"name": "Malaquias", "abbrev": "malaquias", "chapters": 3},
    {"name": "Mateus", "abbrev": "evangelho-segundo-sao-mateus", "chapters": 28},
    {"name": "Marcos", "abbrev": "evangelho-segundo-sao-marcos", "chapters": 16},
    {"name": "Lucas", "abbrev": "evangelho-segundo-sao-lucas", "chapters": 24},
    {"name": "João", "abbrev": "evangelho-segundo-sao-joao", "chapters": 21},
    {"name": "Atos", "abbrev": "atos-dos-apostolos", "chapters": 28},
    {"name": "Romanos", "abbrev": "carta-aos-romanos", "chapters": 16},
    {"name": "1 Coríntios", "abbrev": "primeira-carta-aos-corintios", "chapters": 16},
    {"name": "2 Coríntios", "abbrev": "segunda-carta-aos-corintios", "chapters": 13},
    {"name": "Gálatas", "abbrev": "carta-aos-galatas", "chapters": 6},
    {"name": "Efésios", "abbrev": "carta-aos-efesios", "chapters": 6},
    {"name": "Filipenses", "abbrev": "carta-aos-filipenses", "chapters": 4},
    {"name": "Colossenses", "abbrev": "carta-aos-colossenses", "chapters": 4},
    {
        "name": "1 Tessalonicenses",
        "abbrev": "primeira-carta-aos-tessalonicenses",
        "chapters": 5,
    },
    {
        "name": "2 Tessalonicenses",
        "abbrev": "segunda-carta-aos-tessalonicenses",
        "chapters": 3,
    },
    {"name": "1 Timóteo", "abbrev": "primeira-carta-a-timoteo", "chapters": 6},
    {"name": "2 Timóteo", "abbrev": "segunda-carta-a-timoteo", "chapters": 4},
    {"name": "Tito", "abbrev": "carta-a-tito", "chapters": 3},
    {"name": "Filemom", "abbrev": "carta-a-filemon", "chapters": 1},
    {"name": "Hebreus", "abbrev": "carta-aos-hebreus", "chapters": 13},
    {"name": "Tiago", "abbrev": "carta-de-sao-tiago", "chapters": 5},
    {"name": "1 Pedro", "abbrev": "primeira-carta-de-sao-pedro", "chapters": 5},
    {"name": "2 Pedro", "abbrev": "segunda-carta-de-sao-pedro", "chapters": 3},
    {"name": "1 João", "abbrev": "primeira-carta-de-sao-joao", "chapters": 5},
    {"name": "2 João", "abbrev": "segunda-carta-de-sao-joao", "chapters": 1},
    {"name": "3 João", "abbrev": "terceira-carta-de-sao-joao", "chapters": 1},
    {"name": "Judas", "abbrev": "carta-de-sao-judas", "chapters": 1},
    {"name": "Apocalipse", "abbrev": "apocalipse-de-sao-joao", "chapters": 22},
]

ABBREV_IDX: list[str] = [
    "gn",
    "ex",
    "lv",
    "nm",
    "dt",
    "js",
    "jz",
    "rt",
    "1sm",
    "2sm",
    "1rs",
    "2rs",
    "1cr",
    "2cr",
    "ed",
    "ne",
    "tb",
    "jt",
    "et",
    "1mc",
    "2mc",
    "jó",
    "sl",
    "pv",
    "ec",
    "ct",
    "sb",
    "si",
    "is",
    "jr",
    "lm",
    "br",
    "ez",
    "dn",
    "os",
    "jl",
    "am",
    "ob",
    "jn",
    "mq",
    "na",
    "hc",
    "sf",
    "ag",
    "zc",
    "ml",
    # NT
    "mt",
    "mc",
    "lc",
    "jo",
    "at",
    "rm",
    "1co",
    "2co",
    "gl",
    "ef",
    "fp",
    "cl",
    "1ts",
    "2ts",
    "1tm",
    "2tm",
    "tt",
    "fm",
    "hb",
    "tg",
    "1pe",
    "2pe",
    "1jo",
    "2jo",
    "3jo",
    "jd",
    "ap",
]

GROUPS = [
    "pentateuco",
    "livros-historicos",
    "primeiro-e-segundo-samuel",
    "primeiro-e-segundo-reis",
    "a-historia-desde-adao-ate-a-fundacao-do-judaismo",
    "esdras-e-neemias",
    "livros-sapienciais",
    "livros-profeticos",
    "evangelhos",
]


def main():
    for idx, book in enumerate(BOOKS):
        title = book["name"]
        book_name = book["abbrev"]
        chapters = book["chapters"]

        abbrev = ABBREV_IDX[idx]

        meta = OutputMeta(
            title=title,
            abbrev=abbrev,
        )

        _download_version(meta, abbrev, book_name, chapters, BR_OUTPUT_DIR)


if __name__ == "__main__":
    # ch = _pull_chapter()
    # print(ch)
    main()
