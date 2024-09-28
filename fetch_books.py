import requests
from pathlib import Path
import json

OUTPUT_FILE = Path("./json/books.json")
LIST_BOOKS = "https://www.abibliadigital.com.br/api/books"


def main():
    resp = requests.get(LIST_BOOKS).json()
    with open(OUTPUT_FILE, "w") as f:
        f.write(json.dumps(resp, indent=4))

if __name__ == "__main__":
    main()
