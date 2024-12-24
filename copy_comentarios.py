from collections import defaultdict
import re
from time import sleep
from rich import print
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import typing as t
import json


BR_OUTPUT_DIR = Path("./json/comments/pt-br/")

class BookRef(t.TypedDict):
    name: str
    abbrev: str
    chapters: int

GET_CHAPTER = "https://www.bibliatodo.com/pt/comentarios-da-biblia?v=ACF&&co={COMMENT_VERSION}&l={BOOK}&cap={CHAPTER}"
BR_VERSIONS = ["diario-viver"]

CommentsOutput = dict[str, list[str]]
"""verse -> [comment1, comment2, comment3]"""

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
}

SIMPLE_VERSE_PATTERN = r'^\d+\.(\d+)(ss)? (.*)'
"""e.g. 1.1ss Comentário..."""
RANGE_VERSE_PATTERN = r'^(\d+\.\d+)-(\d+\.\d+) (.*)'
"""e.g. 1.3-2.7 Comentários..."""

def compact_json(raw) -> str:
    return json.dumps(raw, separators=(',', ':')).replace("\n", "")

def _trim_html(raw_html: str) -> str:
    return BeautifulSoup(raw_html, 'html.parser').get_text(strip=True)

def _pull_chapter_comments(comment_version: str, book: str, chapter: int) -> CommentsOutput:
    resp = requests.get(GET_CHAPTER.format(COMMENT_VERSION=comment_version, BOOK=book, CHAPTER=chapter), headers=headers)
    resp.raise_for_status()
    raw_html = resp.text

    soup = BeautifulSoup(raw_html, 'html.parser')
    comments: CommentsOutput = defaultdict(list)

    comments_div = soup.find('div', id='comentariouno')
    if not comments_div:
        print(f"[yellow]Nenhum comentário encontrado para {book} capítulo {chapter}.[/yellow]")
        return comments

    all_comments = comments_div.find('p')
    comm_group = all_comments.decode_contents().split("<br/><br/>")

    def _append_comment(verse: str, raw_comment: str) -> None:
        comments[verse].append(_trim_html(raw_comment))

    for comm in comm_group:
        if match := re.match(SIMPLE_VERSE_PATTERN, comm):
            verse = match.group(1)
            raw_comm = match.group(3)

            _append_comment(verse, raw_comm)

        elif match := re.match(RANGE_VERSE_PATTERN, comm):
            verse_range = match.group(1)
            first_verse = int(verse_range.split(".")[1])
            raw_comm = match.group(3)

            _append_comment(first_verse, raw_comm)

        else:
            pass
            # comments["CHAPTER"].append(comm)

    return comments

def _download_version(version: str, abbrev: str, chapters: int, output_dir: Path) -> None:
    try:
        for ch in range(1, chapters +1):
            filepath_abbrev = SHORT_ABBREV_MAP[abbrev]
            output_file = output_dir / version / filepath_abbrev / f"{ch}.json"
            if output_file.exists():
                continue

            for attempt in range(3):
              try:
                chapter_comments = _pull_chapter_comments(version, abbrev, ch)
                break
              except Exception as e:
                print(f"[red]Attempt {attempt + 1} failed:[/red] {e}")
                if attempt < 2:
                  print("[yellow]Retrying in 10 seconds...[/yellow]")
                  sleep(10)
                else:
                  raise

            if not chapter_comments:
                continue

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(compact_json(chapter_comments))

            print(f"Write [green]{output_file}[/green]")
    except Exception:
        print(f"Error on [red]{abbrev}[/red]")
        raise

BOOKS: list[BookRef] = [
    {"name": "Gênesis",              "abbrev": "genesis",              "chapters": 50},
    {"name": "Êxodo",                "abbrev": "exodo",                "chapters": 40},
    {"name": "Levítico",             "abbrev": "levitico",             "chapters": 27},
    {"name": "Números",              "abbrev": "numeros",              "chapters": 36},
    {"name": "Deuteronômio",         "abbrev": "deuteronomio",         "chapters": 34},
    {"name": "Josué",                "abbrev": "josue",                "chapters": 24},
    {"name": "Juízes",               "abbrev": "juizes",               "chapters": 21},
    {"name": "Rute",                 "abbrev": "rute",                 "chapters": 4},
    {"name": "1 Samuel",             "abbrev": "1samuel",              "chapters": 31},
    {"name": "2 Samuel",             "abbrev": "2samuel",              "chapters": 24},
    {"name": "1 Reis",               "abbrev": "1reis",                "chapters": 22},
    {"name": "2 Reis",               "abbrev": "2reis",                "chapters": 25},
    {"name": "1 Crônicas",           "abbrev": "1cronicas",            "chapters": 29},
    {"name": "2 Crônicas",           "abbrev": "2cronicas",            "chapters": 36},
    {"name": "Esdras",               "abbrev": "esdras",               "chapters": 10},
    {"name": "Neemias",              "abbrev": "neemias",              "chapters": 13},
    {"name": "Ester",                "abbrev": "ester",                "chapters": 10},
    {"name": "Jó",                   "abbrev": "jó",                   "chapters": 42},
    {"name": "Salmos",               "abbrev": "salmos",               "chapters": 150},
    {"name": "Provérbios",           "abbrev": "proverbios",           "chapters": 31},
    {"name": "Eclesiastes",          "abbrev": "eclesiastes",          "chapters": 12},
    {"name": "Cântico dos Cânticos", "abbrev": "canticos",             "chapters": 8},
    {"name": "Isaías",               "abbrev": "isaias",               "chapters": 66},
    {"name": "Jeremias",             "abbrev": "jeremias",             "chapters": 52},
    {"name": "Lamentações",          "abbrev": "lamentacoes",          "chapters": 5},
    {"name": "Ezequiel",             "abbrev": "ezequiel",             "chapters": 48},
    {"name": "Daniel",               "abbrev": "daniel",               "chapters": 12},
    {"name": "Oseias",               "abbrev": "oseias",               "chapters": 14},
    {"name": "Joel",                 "abbrev": "joel",                 "chapters": 3},
    {"name": "Amós",                 "abbrev": "amos",                 "chapters": 9},
    {"name": "Obadias",              "abbrev": "obadias",              "chapters": 1},
    {"name": "Jonas",                "abbrev": "jonas",                "chapters": 4},
    {"name": "Miquéias",             "abbrev": "miqueias",             "chapters": 7},
    {"name": "Naum",                 "abbrev": "naum",                 "chapters": 3},
    {"name": "Habacuque",            "abbrev": "habacuque",            "chapters": 3},
    {"name": "Sofonias",             "abbrev": "sofonias",             "chapters": 3},
    {"name": "Ageu",                 "abbrev": "ageu",                 "chapters": 2},
    {"name": "Zacarias",             "abbrev": "zacarias",             "chapters": 14},
    {"name": "Malaquias",            "abbrev": "malaquias",            "chapters": 3},
    {"name": "Mateus",               "abbrev": "mateus",               "chapters": 28},
    {"name": "Marcos",               "abbrev": "marcos",               "chapters": 16},
    {"name": "Lucas",                "abbrev": "lucas",                "chapters": 24},
    {"name": "João",                 "abbrev": "joao",                 "chapters": 21},
    {"name": "Atos",                 "abbrev": "atos",                 "chapters": 28},
    {"name": "Romanos",              "abbrev": "romanos",              "chapters": 16},
    {"name": "1 Coríntios",          "abbrev": "1corintios",           "chapters": 16},
    {"name": "2 Coríntios",          "abbrev": "2corintios",           "chapters": 13},
    {"name": "Gálatas",              "abbrev": "galatas",              "chapters": 6},
    {"name": "Efésios",              "abbrev": "efesios",              "chapters": 6},
    {"name": "Filipenses",           "abbrev": "filipenses",           "chapters": 4},
    {"name": "Colossenses",          "abbrev": "colossenses",          "chapters": 4},
    {"name": "1 Tessalonicenses",    "abbrev": "1tessalonicenses",     "chapters": 5},
    {"name": "2 Tessalonicenses",    "abbrev": "2tessalonicenses",     "chapters": 3},
    {"name": "1 Timóteo",            "abbrev": "1timoteo",             "chapters": 6},
    {"name": "2 Timóteo",            "abbrev": "2timoteo",             "chapters": 4},
    {"name": "Tito",                 "abbrev": "tito",                 "chapters": 3},
    {"name": "Filemom",              "abbrev": "filemom",              "chapters": 1},
    {"name": "Hebreus",              "abbrev": "hebreus",              "chapters": 13},
    {"name": "Tiago",                "abbrev": "tiago",                "chapters": 5},
    {"name": "1 Pedro",              "abbrev": "1pedro",               "chapters": 5},
    {"name": "2 Pedro",              "abbrev": "2pedro",               "chapters": 3},
    {"name": "1 João",               "abbrev": "1joao",                "chapters": 5},
    {"name": "2 João",               "abbrev": "2joao",                "chapters": 1},
    {"name": "3 João",               "abbrev": "3joao",                "chapters": 1},
    {"name": "Judas",                "abbrev": "judas",                "chapters": 1},
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
    "1samuel": "1sm",
    "2samuel": "2sm",
    "1reis": "1rs",
    "2reis": "2rs",
    "1cronicas": "1cr",
    "2cronicas": "2cr",
    "esdras": "ed",
    "neemias": "ne",
    "ester": "et",
    "jó": "jó",
    "salmos": "sl",
    "proverbios": "pv",
    "eclesiastes": "ec",
    "canticos": "ct",
    "isaias": "is",
    "jeremias": "jr",
    "lamentacoes": "lm",
    "ezequiel": "ez",
    "daniel": "dn",
    "oseias": "os",
    "joel": "jl",
    "amos": "am",
    "obadias": "ob",
    "jonas": "jn",
    "miqueias": "mq",
    "naum": "na",
    "habacuque": "hc",
    "sofonias": "sf",
    "ageu": "ag",
    "zacarias": "zc",
    "malaquias": "ml",
    "mateus": "mt",
    "marcos": "mc",
    "lucas": "lc",
    "joao": "jo",
    "atos": "at",
    "romanos": "rm",
    "1corintios": "1co",
    "2corintios": "2co",
    "galatas": "gl",
    "efesios": "ef",
    "filipenses": "fp",
    "colossenses": "cl",
    "1tessalonicenses": "1ts",
    "2tessalonicenses": "2ts",
    "1timoteo": "1tm",
    "2timoteo": "2tm",
    "tito": "tt",
    "filemom": "fm",
    "hebreus": "hb",
    "tiago": "tg",
    "1pedro": "1pe",
    "2pedro": "2pe",
    "1joao": "1jo",
    "2joao": "2jo",
    "3joao": "3jo",
    "judas": "jd",
    "apocalipse": "ap",
}

def main():
    for book in BOOKS:
        abbrev = book["abbrev"]
        chapters = book["chapters"]

        for version in BR_VERSIONS:
            _download_version(version, abbrev, chapters, BR_OUTPUT_DIR)


if __name__ == "__main__":
    main()
