import csv
import tempfile
import unittest
from pathlib import Path

from doc_triage.config import load_categories
from doc_triage.input import collect_requests
from doc_triage.report import ReportRow, safe_cell, write_report
from doc_triage.triage import TriageResult


class TriageCoreTests(unittest.TestCase):
    def test_input_and_sorted_csv_report(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.txt").write_text("Не могу войти", encoding="utf-8")
            (root / "b.csv").write_text('id,text\n42,"Нужен счёт"\n', encoding="utf-8")
            requests = collect_requests(root)
            self.assertEqual([item.source for item in requests], ["a.txt", "b.csv:42"])
            rows = [
                ReportRow(
                    source=requests[0].source,
                    text=requests[0].text,
                    result=TriageResult("Поддержка", "Вход", "high", ["кабинет"]),
                ),
                ReportRow(
                    source=requests[1].source,
                    text=requests[1].text,
                    result=TriageResult("Оплата", "Счёт", "medium", []),
                ),
            ]
            output = root / "report.csv"
            write_report(output, rows, ["Оплата", "Поддержка"])
            with output.open(encoding="utf-8-sig", newline="") as file:
                data = list(csv.reader(file))
            self.assertEqual(data[1][1], "Оплата")
            self.assertEqual(data[2][1], "Поддержка")

    def test_invalid_categories_and_formula_escape(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "categories.json"
            path.write_text('["A", "A"]', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_categories(path)
        self.assertEqual(safe_cell("=1+1"), "'=1+1")
        self.assertEqual(safe_cell("Обычный текст"), "Обычный текст")


if __name__ == "__main__":
    unittest.main()