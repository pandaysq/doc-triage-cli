import json
from pathlib import Path


def load_categories(path: Path) -> list[str]:
    try:
        categories = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Не удалось прочитать категории из {path}: {error}") from error
    if (
        not isinstance(categories, list)
        or not categories
        or not all(isinstance(item, str) and item.strip() for item in categories)
        or len(categories) != len(set(categories))
    ):
        raise ValueError("categories.json должен содержать непустой список уникальных строк")
    return categories