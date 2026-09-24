import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from .config import load_categories
from .input import collect_requests
from .report import ReportRow, write_report
from .triage import TriageClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="doc-triage-cli",
        description="Классифицирует обращения и создаёт отчёт CSV/Excel",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    process = subcommands.add_parser("process", help="Обработать .txt и .csv в папке")
    process.add_argument("input_folder", type=Path)
    process.add_argument("--output", type=Path, default=Path("report.xlsx"))
    process.add_argument(
        "--categories",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "categories.json",
    )
    process.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args(argv)

    try:
        if args.output.suffix.lower() not in (".csv", ".xlsx"):
            raise ValueError("--output должен заканчиваться на .csv или .xlsx")
        if args.max_retries < 1 or args.max_retries > 10:
            raise ValueError("--max-retries должен быть от 1 до 10")
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_api_key_here":
            raise ValueError("Установите ANTHROPIC_API_KEY в окружении или .env")
        categories = load_categories(args.categories)
        requests = collect_requests(args.input_folder)
        client = TriageClient(
            api_key=api_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            categories=categories,
            max_retries=args.max_retries,
        )
        rows: list[ReportRow] = []
        failures = 0
        for request in tqdm(requests, desc="Обработка запросов", unit="запрос"):
            try:
                result = client.classify(request.text)
                rows.append(ReportRow(source=request.source, text=request.text, result=result))
            except Exception as error:
                failures += 1
                rows.append(
                    ReportRow(
                        source=request.source,
                        text=request.text,
                        result=None,
                        error=f"{type(error).__name__}: {error}",
                    )
                )
                tqdm.write(f"Ошибка в {request.source}: {type(error).__name__}: {error}")
        write_report(args.output, rows, categories)
        print(f"Готово: {args.output} ({len(rows)} запросов, ошибок: {failures})")
        return 1 if failures else 0
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2