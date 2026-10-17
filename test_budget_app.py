import csv
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from Main import main
from Transaction import Transaction, check_amount, check_date
from Transaction_Control import TransactionControl
from Budget import check_month
from Load_data import load_data
from Save_data import save_data, CSV_FIELDS


class BudgetAppTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.control = TransactionControl(self.folder / "data")
        self.call(["category", "add", "food"])
        self.call(["category", "add", "salary"])

    def call(self, args):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            code = main(args, self.control)
        return code, output.getvalue()

    def add(self, date="2026-10-17", amount="100", category="food", type="expense"):
        return self.control.add_transaction(Transaction(type, amount, category, date))

    def write_import(self, rows, fields=CSV_FIELDS):
        path = self.folder / "import.csv"
        save_data(path, rows, fields)
        return str(path)

    def test_initialization_and_persistence(self):
        self.assertEqual(len(list((self.folder / "data").glob("*.csv"))), 3)
        identifier = self.add()
        self.control.budget.edit_budget("500", "2026-10")
        restarted = TransactionControl(self.folder / "data")
        self.assertEqual(next(restarted.show_transactions())["id"], identifier)
        self.assertEqual(restarted.budget.get_budget("2026-10"), 500)
        restarted.check_category("food")

    def test_interactive_add_and_category(self):
        with patch("builtins.input", side_effect=["rent"]):
            self.assertEqual(self.call(["category", "add"])[0], 0)
        with patch("builtins.input", side_effect=["2026-10-17", "expense", "rent", "500", "", ""]):
            code, output = self.call(["add"])
        self.assertEqual(code, 0)
        self.assertIn("ID:", output)
        self.assertEqual(next(self.control.show_transactions())["category"], "rent")

    def test_option_add_does_not_prompt(self):
        with patch("builtins.input", side_effect=AssertionError("unexpected prompt")):
            code, _ = self.call(["add", "--date", "2026-10-17", "--type", "expense",
                                 "--category", "food", "--amount", "500"])
        self.assertEqual(code, 0)

    def test_invalid_inputs_do_not_write(self):
        before = self.control.path.read_bytes()
        for amount in ["0", "-1", "1.5", "NaN", "Infinity", "abc"]:
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                check_amount(amount)
        for date in ["2026-02-30", "2026-1-01", "bad"]:
            with self.subTest(date=date), self.assertRaises(ValueError):
                check_date(date)
        for month in ["2026-13", "2026-1"]:
            with self.assertRaises(ValueError):
                check_month(month)
        with self.assertRaises(ValueError):
            Transaction("other", "100", "food", "2026-10-17")
        with self.assertRaises(ValueError):
            self.add(category="missing")
        self.assertEqual(self.control.path.read_bytes(), before)

    def test_latest_order_limit_and_search(self):
        self.add("2026-10-10")
        latest = self.add("2026-10-20")
        self.add("2026-10-01")
        tagged = Transaction("expense", "200", "food", "2026-10-20", "Lunch", "meal, school")
        identifier = self.control.add_transaction(tagged)
        self.assertEqual([row["id"] for row in self.control.show_transactions(2)], [identifier, latest])
        result = list(self.control.search_transactions("2026-10-20", "2026-10-20", "food", "expense", "lunch", "school"))
        self.assertEqual([row["id"] for row in result], [identifier])
        for args in [["list", "--limit", "0"], ["search", "--from", "2026-11-01", "--to", "2026-10-01"]]:
            self.assertEqual(self.call(args)[0], 1)

    def test_update_delete_and_invalid_updates(self):
        identifier = self.add()
        self.assertEqual(self.call(["update", "--id", identifier, "--amount", "300", "--memo", ""])[0], 0)
        self.assertEqual(next(self.control.show_transactions())["amount"], "300")
        before = self.control.path.read_bytes()
        for args in [["update", "--id", identifier, "--amount", "-1"],
                     ["update", "--id", "missing", "--amount", "5"],
                     ["delete", "--id", "missing"]]:
            self.assertEqual(self.call(args)[0], 1)
            self.assertEqual(self.control.path.read_bytes(), before)
        self.assertEqual(self.call(["delete", "--id", identifier])[0], 0)
        self.assertEqual(list(self.control.show_transactions()), [])

    def test_used_category_cannot_be_removed(self):
        identifier = self.add()
        self.assertEqual(self.call(["category", "remove", "food"])[0], 1)
        self.control.delete_transaction(identifier)
        self.assertEqual(self.call(["category", "remove", "food"])[0], 0)
        self.assertEqual(self.call(["category", "add", "salary"])[0], 1)

    def test_summary_budget_warning_and_empty_month(self):
        self.add(amount="150")
        self.add(amount="1000", category="salary", type="income")
        self.assertEqual(self.call(["budget", "set", "--month", "2026-10", "--amount", "100"])[0], 0)
        code, output = self.call(["summary", "--month", "2026-10", "--top", "1"])
        self.assertEqual(code, 0)
        for text in ["총 수입: 1000", "총 지출: 150", "잔액: 850", "food: 150", "150.00%", "초과"]:
            self.assertIn(text, output)
        self.assertIn("데이터 없음", self.call(["summary", "--month", "2026-09"])[1])

    def test_export_import_roundtrip(self):
        self.control.add_transaction(Transaction("expense", "8000", "food", "2026-10-17", '점심,"식사"\n메모', "학교,식사"))
        self.add("2026-09-01")
        output = self.folder / "export.csv"
        self.assertEqual(self.control.export_transactions(str(output), month="2026-10"), 1)
        with output.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(list(rows[0]), CSV_FIELDS)
        self.assertEqual(rows[0]["tags"], "학교,식사")
        self.assertEqual(self.control.import_transactions(str(output)), 1)
        records = list(self.control.show_transactions())
        self.assertEqual(len({row["id"] for row in records}), 3)
        self.assertEqual(records[0]["memo"], '점심,"식사"\n메모')

    def test_import_failure_is_atomic(self):
        self.add()
        before = self.control.path.read_bytes()
        good = dict(date="2026-10-17", type="expense", category="food", amount="300", memo="", tags="")
        source = self.write_import([good, dict(good, amount="-1")])
        code, output = self.call(["import", "--from", source])
        self.assertEqual(code, 1)
        self.assertIn("3번째 줄", output)
        self.assertEqual(self.control.path.read_bytes(), before)

    def test_import_optional_columns_and_bad_header(self):
        source = self.write_import([dict(date="2026-10-17", type="expense", category="food", amount="300")], CSV_FIELDS[:4])
        self.assertEqual(self.call(["import", "--from", source])[0], 0)
        self.assertEqual(next(self.control.show_transactions())["tags"], "")
        Path(source).write_text("date,type,category,amount,amount\n", encoding="utf-8")
        self.assertEqual(self.call(["import", "--from", source])[0], 1)

    def test_export_filters_and_protects_files(self):
        self.add("2026-10-17")
        self.add("2026-09-01")
        output = self.folder / "export.csv"
        self.assertEqual(self.control.export_transactions(str(output), start="2026-10-17", end="2026-10-17"), 1)
        before = output.read_bytes()
        for args in [[], ["--from", "2026-10-01"], ["--month", "2026-10", "--to", "2026-10-31"],
                     ["--from", "2026-11-01", "--to", "2026-10-01"]]:
            self.assertEqual(self.call(["export", "--out", str(output)] + args)[0], 1)
            self.assertEqual(output.read_bytes(), before)
        for stored in (self.folder / "data").glob("*.csv"):
            before_stored = stored.read_bytes()
            self.assertEqual(self.call(["export", "--out", str(stored), "--month", "2026-10"])[0], 1)
            self.assertEqual(stored.read_bytes(), before_stored)
        self.assertEqual(self.control.export_transactions(str(output), month="2025-01"), 0)

    def test_failed_write_keeps_original_and_cleans_temporary(self):
        self.add()
        before = self.control.path.read_bytes()
        with patch("Save_data.csv.DictWriter.writerows", side_effect=OSError("disk full")):
            self.assertEqual(self.call(["delete", "--id", next(self.control.show_transactions())["id"]])[0], 1)
        self.assertEqual(self.control.path.read_bytes(), before)
        self.assertEqual(list(self.control.path.parent.glob("*.tmp")), [])
        with patch("Save_data.Path.replace", side_effect=OSError("replace failed")):
            self.assertEqual(self.call(["budget", "set", "--month", "2026-10", "--amount", "100"])[0], 1)
        self.assertEqual(list(self.control.path.parent.glob("*.tmp")), [])

    def test_load_is_lazy_and_reports_corruption(self):
        self.add()
        with self.control.path.open("a", encoding="utf-8") as file:
            file.write("broken,row\n")
        self.assertEqual(len(list(self.control.show_transactions(1))), 1)
        code, output = self.call(["list"])
        self.assertEqual(code, 1)
        self.assertNotIn("Traceback", output)

    def test_help_for_every_command(self):
        commands = [[], ["add"], ["list"], ["search"], ["summary"], ["budget"],
                    ["budget", "set"], ["category"], ["category", "add"],
                    ["category", "list"], ["category", "remove"], ["update"],
                    ["delete"], ["import"], ["export"]]
        for command in commands:
            with self.subTest(command=command), self.assertRaises(SystemExit) as raised:
                self.call(command + ["--help"])
            self.assertEqual(raised.exception.code, 0)

    def test_stored_invalid_values_are_rejected_without_writing(self):
        from Save_data import FIELDS
        row = Transaction("expense", "100", "food", "2026-10-17").to_dict()
        for field, value in [("type", "wrong"), ("amount", "-100"),
                             ("date", "2026-02-30"), ("category", "missing"), ("id", "")]:
            bad = row.copy()
            bad[field] = value
            save_data(self.control.path, [bad], FIELDS["transactions"])
            before = self.control.path.read_bytes()
            for command in [["list"], ["summary", "--month", "2026-10"],
                            ["delete", "--id", row["id"]]]:
                code, output = self.call(command)
                self.assertEqual(code, 1)
                self.assertNotIn("Traceback", output)
                self.assertEqual(self.control.path.read_bytes(), before)

    def test_legacy_file_read_and_safe_conversion(self):
        old_fields = ["type", "money", "category", "date", "memo", "tag", "id"]
        row = dict(type="expense", money="100", category="food",
                   date="2026-10-17", memo="기존 메모", tag="meal", id="old-id")
        save_data(self.control.path, [row], old_fields)
        before = self.control.path.read_bytes()
        loaded = next(self.control.show_transactions())
        self.assertEqual(loaded["amount"], "100")
        self.assertEqual(loaded["tags"], "meal")
        self.assertEqual(self.control.path.read_bytes(), before)
        self.assertEqual(self.call(["update", "--id", "old-id", "--amount", "200"])[0], 0)
        with self.control.path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            self.assertIn("amount", reader.fieldnames)
            self.assertNotIn("money", reader.fieldnames)
            updated = next(reader)
            self.assertEqual(updated["id"], "old-id")
            self.assertEqual(updated["memo"], "기존 메모")
            self.assertEqual(updated["amount"], "200")

    def test_blank_search_dates_are_errors(self):
        for option in ["--from", "--to"]:
            code, output = self.call(["search", option, ""])
            self.assertEqual(code, 1)
            self.assertNotIn("Traceback", output)

    def test_actual_exit_codes_and_interactive_recovery(self):
        base = [sys.executable, str(Path(__file__).with_name("Main.py")), "--data-dir", str(self.control.path.parent)]
        result = subprocess.run(base + ["delete", "--id", "missing"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        result = subprocess.run(base + ["list"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        result = subprocess.run(base, input="unknown\nlist\nexit\n", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("데이터 없음", result.stdout)
        result = subprocess.run(base, input="unknown\nexit\n", capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
