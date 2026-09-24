import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Request:
    source: str
    text: str


def collect_requests(folder: Path) -> list[Request]:
    if not folder.is_dir():
        raise ValueError(f"Входная папка не найдена: {folder}")
    results: list[Request] = []
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8").strip()
            if text:
                results.append(Request(source=path.name, text=text))
        elif path.suffix.lower() == ".csv":
            with path.open(newline="", encoding="utf-8-sig") as source:
                reader = csv.DictReader(source)
                if not reader.fieldnames or "text" not in reader.fieldnames:
                    raise ValueError(f"{path.name}: CSV должен содержать столбец text")
                for line, row in enumerate(reader, start=2):
                    text = (row.get("text") or "").strip()
                    if text:
                        identifier = (row.get("id") or "").strip()
                        name = identifier if identifier else f"строка {line}"
                        results.append(Request(source=f"{path.name}:{name}", text=text))
    if not results:
        raise ValueError("Во входной папке нет непустых .txt или .csv с запросами")
    return results