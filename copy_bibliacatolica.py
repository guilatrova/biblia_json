import re
from time import sleep
from rich import print
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import typing as t
import json


BR_OUTPUT_DIR = Path("./json/catolicos/pt-br/")
US_OUTPUT_DIR = Path("./json/catolicos/en-us/")

class OutputMeta(t.TypedDict):
    title: str
    abbrev: str

class Output(t.TypedDict):
    meta: OutputMeta
    chapter: int
    content: dict[str, str]
    titles: t.NotRequired[dict[str, str]]

GET_CHAPTER = "https://www.bibliacatolica.com.br/{VERSION}/{ABBREV}/{CHAPTER}/"
BR_VERSIONS = ["biblia-ave-maria"]
US_VERSIONS = []


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
}

def compact_json(raw) -> str:
    return json.dumps(raw, separators=(',', ':')).replace("\n", "")

def _pull_chapter(version: str, abbrev: str, chapter: int) -> dict[str, str]:
    resp = requests.get(GET_CHAPTER.format(VERSION=version, ABBREV=abbrev, CHAPTER=chapter), headers=headers)
    resp.raise_for_status()
    raw_html = resp.text

    soup = BeautifulSoup(raw_html, 'html.parser')
    verses: dict[str, str] = {}

    section = soup.find('section', class_='entry clearfix')
    if not section:
        return {}
    for span in section.find_all('span', class_='html-tag'):
        span.decompose()
    full_text = ' '.join(section.stripped_strings)
    pattern = re.compile(r'(\d+)\.\s*(.*?)\s*(?=\d+\.|$)', re.DOTALL)
    verses = {num: ' '.join(text.split()) for num, text in pattern.findall(full_text)}

    return verses

def _download_version(meta: OutputMeta, version: str, abbrev: str, chapters: int, output_dir: Path) -> None:
    try:
        for ch in range(1, chapters +1):
            filepath_abbrev = SHORT_ABBREV_MAP[abbrev]
            output_file = output_dir / "ave-maria" / filepath_abbrev / f"{ch}.json"
            if output_file.exists() and len(json.loads(output_file.read_text())["content"]) > 0:
                continue

            for attempt in range(3):
              try:
                chapter_content = _pull_chapter(version, abbrev, ch)
                if len(chapter_content) == 0:
                  print(f"[red]Empty chapter {abbrev} {ch}[/red]")
                  continue
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
        print(f"Error on [red]{meta['title']}[/red]")
        raise

class BookRef(t.TypedDict):
    name: str
    abbrev: str
    chapters: int

BOOKS: list[BookRef] = [
    {"name": "Gênesis",              "abbrev": "genesis",              "chapters": 50},
    {"name": "Êxodo",                "abbrev": "exodo",                "chapters": 40},
    {"name": "Levítico",             "abbrev": "levitico",             "chapters": 27},
    {"name": "Números",              "abbrev": "numeros",              "chapters": 36},
    {"name": "Deuteronômio",         "abbrev": "deuteronomio",         "chapters": 34},
    {"name": "Josué",                "abbrev": "josue",                "chapters": 24},
    {"name": "Juízes",               "abbrev": "juizes",               "chapters": 21},
    {"name": "Rute",                 "abbrev": "rute",                 "chapters": 4},
    {"name": "1 Samuel",             "abbrev": "i-samuel",             "chapters": 31},
    {"name": "2 Samuel",             "abbrev": "ii-samuel",            "chapters": 24},
    {"name": "1 Reis",               "abbrev": "i-reis",               "chapters": 22},
    {"name": "2 Reis",               "abbrev": "ii-reis",              "chapters": 25},
    {"name": "1 Crônicas",           "abbrev": "i-cronicas",           "chapters": 29},
    {"name": "2 Crônicas",           "abbrev": "ii-cronicas",          "chapters": 36},
    {"name": "Esdras",               "abbrev": "esdras",               "chapters": 10},
    {"name": "Neemias",              "abbrev": "neemias",              "chapters": 13},
    {"name": "Tobias",               "abbrev": "tobias",               "chapters": 14},
    {"name": "Judite",               "abbrev": "judite",               "chapters": 16},
    {"name": "Ester",                "abbrev": "ester",                "chapters": 10},
    {"name": "1 Macabeus",           "abbrev": "i-macabeus",           "chapters": 16},
    {"name": "2 Macabeus",           "abbrev": "ii-macabeus",          "chapters": 15},
    {"name": "Jó",                   "abbrev": "jo",                   "chapters": 42},
    {"name": "Salmos",               "abbrev": "salmos",               "chapters": 150},
    {"name": "Provérbios",           "abbrev": "proverbios",           "chapters": 31},
    {"name": "Eclesiastes",          "abbrev": "eclesiastes",          "chapters": 12},
    {"name": "Cântico dos Cânticos", "abbrev": "cantico-dos-canticos", "chapters": 8},
    {"name": "Sabedoria",            "abbrev": "sabedoria",            "chapters": 19},
    {"name": "Eclesiástico",         "abbrev": "eclesiastico",         "chapters": 51},
    {"name": "Isaías",               "abbrev": "isaias",               "chapters": 66},
    {"name": "Jeremias",             "abbrev": "jeremias",             "chapters": 52},
    {"name": "Lamentações",          "abbrev": "lamentacoes",          "chapters": 5},
    {"name": "Baruc",                "abbrev": "baruc",                "chapters": 6},
    {"name": "Ezequiel",             "abbrev": "ezequiel",             "chapters": 48},
    {"name": "Daniel",               "abbrev": "daniel",               "chapters": 14},
    {"name": "Oseias",               "abbrev": "oseias",               "chapters": 14},
    {"name": "Joel",                 "abbrev": "joel",                 "chapters": 4},
    {"name": "Amós",                 "abbrev": "amos",                 "chapters": 9},
    {"name": "Obadias",              "abbrev": "abdias",               "chapters": 1},
    {"name": "Jonas",                "abbrev": "jonas",                "chapters": 4},
    {"name": "Miquéias",             "abbrev": "miqueias",             "chapters": 7},
    {"name": "Naum",                 "abbrev": "naum",                 "chapters": 3},
    {"name": "Habacuque",            "abbrev": "habacuc",              "chapters": 3},
    {"name": "Sofonias",             "abbrev": "sofonias",             "chapters": 3},
    {"name": "Ageu",                 "abbrev": "ageu",                 "chapters": 2},
    {"name": "Zacarias",             "abbrev": "zacarias",             "chapters": 14},
    {"name": "Malaquias",            "abbrev": "malaquias",            "chapters": 3},
    {"name": "Mateus",               "abbrev": "sao-mateus",           "chapters": 28},
    {"name": "Marcos",               "abbrev": "sao-marcos",           "chapters": 16},
    {"name": "Lucas",                "abbrev": "sao-lucas",            "chapters": 24},
    {"name": "João",                 "abbrev": "sao-joao",             "chapters": 21},
    {"name": "Atos",                 "abbrev": "atos-dos-apostolos",   "chapters": 28},
    {"name": "Romanos",              "abbrev": "romanos",              "chapters": 16},
    {"name": "1 Coríntios",          "abbrev": "i-corintios",          "chapters": 16},
    {"name": "2 Coríntios",          "abbrev": "ii-corintios",         "chapters": 13},
    {"name": "Gálatas",              "abbrev": "galatas",              "chapters": 6},
    {"name": "Efésios",              "abbrev": "efesios",              "chapters": 6},
    {"name": "Filipenses",           "abbrev": "filipenses",           "chapters": 4},
    {"name": "Colossenses",          "abbrev": "colossenses",          "chapters": 4},
    {"name": "1 Tessalonicenses",    "abbrev": "i-tessalonicenses",    "chapters": 5},
    {"name": "2 Tessalonicenses",    "abbrev": "ii-tessalonicenses",   "chapters": 3},
    {"name": "1 Timóteo",            "abbrev": "i-timoteo",            "chapters": 6},
    {"name": "2 Timóteo",            "abbrev": "ii-timoteo",           "chapters": 4},
    {"name": "Tito",                 "abbrev": "tito",                 "chapters": 3},
    {"name": "Filemom",              "abbrev": "filemon",              "chapters": 1},
    {"name": "Hebreus",              "abbrev": "hebreus",              "chapters": 13},
    {"name": "Tiago",                "abbrev": "sao-tiago",            "chapters": 5},
    {"name": "1 Pedro",              "abbrev": "i-sao-pedro",          "chapters": 5},
    {"name": "2 Pedro",              "abbrev": "ii-sao-pedro",         "chapters": 3},
    {"name": "1 João",               "abbrev": "i-sao-joao",           "chapters": 5},
    {"name": "2 João",               "abbrev": "ii-sao-joao",          "chapters": 1},
    {"name": "3 João",               "abbrev": "iii-sao-joao",         "chapters": 1},
    {"name": "Judas",                "abbrev": "sao-judas",                "chapters": 1},
    {"name": "Apocalipse",           "abbrev": "apocalipse",           "chapters": 22},
]

SHORT_ABBREV_MAP: dict[str, str] = {
    "genesis": "gn",
    "exodo": "ex",
    "levitico": "lv",
    "numeros": "nm",
    "deuteronomio": "dt",
    "josue": "js",
    "juizes": "jz",
    "rute": "rt",
    "i-samuel": "1sm",
    "ii-samuel": "2sm",
    "i-reis": "1rs",
    "ii-reis": "2rs",
    "i-cronicas": "1cr",
    "ii-cronicas": "2cr",
    "esdras": "ed",
    "neemias": "ne",
    "tobias": "tb",
    "judite": "jt",
    "ester": "et",
    "i-macabeus": "1mc",
    "ii-macabeus": "2mc",
    "jo": "jo",
    "salmos": "sl",
    "proverbios": "pv",
    "eclesiastes": "ec",
    "cantico-dos-canticos": "ct",
    "sabedoria": "sb",
    "eclesiastico": "si",
    "isaias": "is",
    "jeremias": "jr",
    "lamentacoes": "lm",
    "baruc": "br",
    "ezequiel": "ez",
    "daniel": "dn",
    "oseias": "os",
    "joel": "jl",
    "amos": "am",
    "abdias": "ob",
    "jonas": "jn",
    "miqueias": "mq",
    "naum": "na",
    "habacuc": "hc",
    "sofonias": "sf",
    "ageu": "ag",
    "zacarias": "zc",
    "malaquias": "ml",
    # NT
    "sao-mateus": "mt",
    "sao-marcos": "mc",
    "sao-lucas": "lc",
    "sao-joao": "jo",
    "atos-dos-apostolos": "at",
    "romanos": "rm",
    "i-corintios": "1co",
    "ii-corintios": "2co",
    "galatas": "gl",
    "efesios": "ef",
    "filipenses": "fp",
    "colossenses": "cl",
    "i-tessalonicenses": "1ts",
    "ii-tessalonicenses": "2ts",
    "i-timoteo": "1tm",
    "ii-timoteo": "2tm",
    "tito": "tt",
    "filemon": "fm",
    "hebreus": "hb",
    "sao-tiago": "tg",
    "i-sao-pedro": "1pe",
    "ii-sao-pedro": "2pe",
    "i-sao-joao": "1jo",
    "ii-sao-joao": "2jo",
    "iii-sao-joao": "3jo",
    "sao-judas": "jd",
    "apocalipse": "ap",
}

def main():
    for book in BOOKS:
        title = book["name"]
        abbrev = book["abbrev"]
        chapters = book["chapters"]

        meta = OutputMeta(
            title=title,
            abbrev=SHORT_ABBREV_MAP[abbrev],
        )

        for version in BR_VERSIONS:
            _download_version(meta, version, abbrev, chapters, BR_OUTPUT_DIR)

        for version in US_VERSIONS:
            _download_version(meta, version, abbrev, chapters, US_OUTPUT_DIR)


if __name__ == "__main__":
    # ch = _pull_chapter("biblia-ave-maria", "genesis", 1)
    # print(ch)
    main()
