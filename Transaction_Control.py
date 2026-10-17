# 거래는 저장할 때 최신 날짜순으로 정렬하고, 조회할 때 한 줄씩 읽습니다.
import csv
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from Load_data import load_data
from Save_data import save_data, initialize, FIELDS, CSV_FIELDS
from Transaction import Transaction, check_date
from Budget import Budget, check_month


class TransactionControl:
    def __init__(self, data_dir: str | Path = "data") -> None:
        folder = initialize(data_dir)
        self.path = folder / "transactions.csv"
        self.category_path = folder / "categories.csv"
        self.budget = Budget(folder)

    def load_transactions(self) -> Iterator[dict[str, str]]:
        # 파일 전체를 담지 않고 거래 한 건씩 확인합니다.
        for row in load_data(self.path):
            try:
                if not row["id"].strip():
                    raise ValueError("거래 ID가 비어 있습니다.")
                transaction = Transaction(**row)
                self.check_category(transaction.category)
            except ValueError as error:
                raise ValueError(f"저장된 거래 {row['id']}: {error} 원본 CSV를 확인하세요.") from None
            yield transaction.to_dict()

    def save_transactions(self, rows: list[dict[str, str]]) -> None:
        rows.sort(key=lambda row: row["date"], reverse=True)
        save_data(self.path, rows, FIELDS["transactions"])

    def check_category(self, name: str) -> None:
        names = [row["name"] for row in load_data(self.category_path)]
        if name not in names:
            raise ValueError("등록되지 않은 카테고리입니다. category add로 먼저 추가하세요.")

    def add_transaction(self, transaction: Transaction) -> str:
        self.check_category(transaction.category)
        rows = list(self.load_transactions())
        ids = {row["id"] for row in rows}
        while transaction.id in ids:
            transaction.id = uuid4().hex[:12]
        rows.insert(0, transaction.to_dict())
        self.save_transactions(rows)
        return transaction.id

    def show_transactions(self, limit: int = 10) -> Iterator[dict[str, str]]:
        if limit <= 0:
            raise ValueError("limit은 1 이상으로 입력하세요.")
        for index, row in enumerate(self.load_transactions()):
            yield row
            if index + 1 >= limit:
                break

    def delete_transaction(self, transaction_id: str) -> None:
        rows = list(self.load_transactions())
        remaining = [row for row in rows if row["id"] != transaction_id]
        if len(rows) == len(remaining):
            raise ValueError("거래 ID를 찾을 수 없습니다. list로 ID를 확인하세요.")
        self.save_transactions(remaining)

    def update_transaction(self, transaction_id: str, changes: dict[str, str]) -> None:
        rows = list(self.load_transactions())
        for index, row in enumerate(rows):
            if row["id"] == transaction_id:
                row = row.copy()
                row.update(changes)
                transaction = Transaction(**row)
                self.check_category(transaction.category)
                rows[index] = transaction.to_dict()
                self.save_transactions(rows)
                return
        raise ValueError("거래 ID를 찾을 수 없습니다. list로 ID를 확인하세요.")

    def search_transactions(self, start: str | None = None, end: str | None = None,
                            category: str | None = None, type: str | None = None,
                            q: str | None = None, tag: str | None = None
                            ) -> Iterator[dict[str, str]]:
        if start is not None:
            check_date(start)
        if end is not None:
            check_date(end)
        if start and end and start > end:
            raise ValueError("시작 날짜는 종료 날짜보다 늦을 수 없습니다.")
        for row in self.load_transactions():
            if start and row["date"] < start:
                continue
            if end and row["date"] > end:
                continue
            if category and row["category"] != category:
                continue
            if type and row["type"] != type:
                continue
            if q and q.casefold() not in row["memo"].casefold():
                continue
            if tag and tag not in [value.strip() for value in row["tags"].split(",")]:
                continue
            yield row

    def summarize_transactions(self, date: str, top: int = 5) -> list[str]:
        check_month(date)
        if top <= 0:
            raise ValueError("top은 1 이상으로 입력하세요.")
        income = Decimal("0")
        expense = Decimal("0")
        categories = {}
        count = 0
        for row in self.load_transactions():
            if row["date"][:7] != date:
                continue
            count += 1
            amount = Decimal(row["amount"])
            if row["type"] == "income":
                income += amount
            else:
                expense += amount
                name = row["category"]
                categories[name] = categories.get(name, Decimal("0")) + amount
        lines = []
        if count == 0:
            lines.append("데이터 없음")
        lines.append(f"총 수입: {income}\n총 지출: {expense}\n잔액: {income - expense}")
        for name, amount in sorted(categories.items(), key=lambda item: item[1], reverse=True)[:top]:
            lines.append(f"{name}: {amount}")
        budget = self.budget.get_budget(date)
        if budget is not None:
            lines.append(f"예산: {budget}, 사용률: {expense / budget * 100:.2f}%")
            if expense > budget:
                lines.append("경고: 예산을 초과했습니다.")
        return lines

    def category(self, action: str, name: str | None = None) -> list[str]:
        rows = list(load_data(self.category_path))
        names = [row["name"] for row in rows]
        if action == "list":
            if not names:
                return ["등록된 카테고리가 없습니다. category add로 추가하세요."]
            return names
        if not name or not name.strip():
            raise ValueError("카테고리 이름을 입력하세요.")
        name = name.strip()
        if action == "add":
            if name in names:
                raise ValueError("이미 등록된 카테고리입니다.")
            rows.append({"name": name})
        elif action == "remove":
            self.check_category(name)
            for transaction in self.load_transactions():
                if transaction["category"] == name:
                    raise ValueError("사용 중인 카테고리입니다. 거래를 수정하거나 삭제한 뒤 다시 시도하세요.")
            rows = [row for row in rows if row["name"] != name]
        else:
            raise ValueError("카테고리 명령은 add, list, remove 중 하나를 입력하세요.")
        save_data(self.category_path, rows, FIELDS["categories"])
        return [f"카테고리 {action} 완료: {name}"]


    def import_transactions(self, source: str) -> int:
        """모든 행을 검증한 다음 한 번에 저장합니다. 오류가 있으면 반영하지 않습니다."""
        rows = list(self.load_transactions())
        ids = {row["id"] for row in rows}
        imported = []
        with Path(source).open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file, strict=True)
            fields = reader.fieldnames or []
            required = {"date", "type", "category", "amount"}
            if (not required.issubset(fields) or len(fields) != len(set(fields))
                    or not set(fields).issubset(CSV_FIELDS)):
                raise ValueError("CSV 헤더를 확인하세요: date,type,category,amount,memo,tags")
            for row in reader:
                if None in row or None in row.values():
                    raise ValueError(f"CSV {reader.line_num}번째 줄의 항목 수를 확인하세요.")
                try:
                    transaction = Transaction(row["type"], row["amount"], row["category"],
                                              row["date"], row.get("memo", ""), row.get("tags", ""))
                    self.check_category(transaction.category)
                except ValueError as error:
                    raise ValueError(f"CSV {reader.line_num}번째 줄: {error}") from None
                while transaction.id in ids:
                    transaction.id = uuid4().hex[:12]
                ids.add(transaction.id)
                imported.append(transaction.to_dict())
        if imported:
            # 같은 날짜에서는 CSV의 뒤쪽 행을 더 나중에 추가한 거래로 취급합니다.
            self.save_transactions(list(reversed(imported)) + rows)
        return len(imported)

    def export_transactions(self, output: str, month: str | None = None,
                            start: str | None = None, end: str | None = None) -> int:
        if month is not None:
            check_month(month)
            if start is not None or end is not None:
                raise ValueError("--month와 --from/--to는 함께 사용하지 마세요.")
        elif start is None or end is None:
            raise ValueError("--month 또는 --from과 --to를 모두 입력하세요.")
        destination = Path(output)
        for name in FIELDS:
            stored = self.path.parent / (name + ".csv")
            if destination.resolve() == stored.resolve():
                raise ValueError("저장 중인 데이터 파일로 내보낼 수 없습니다. 다른 경로를 지정하세요.")
        count = 0

        def export_rows() -> Iterator[dict[str, str]]:
            nonlocal count
            for row in self.search_transactions(start, end):
                if month is not None and row["date"][:7] != month:
                    continue
                count += 1
                yield {"date": row["date"], "type": row["type"],
                       "category": row["category"], "amount": row["amount"],
                       "memo": row["memo"], "tags": row["tags"]}

        save_data(destination, export_rows(), CSV_FIELDS)
        return count


Transaction_Control = TransactionControl
