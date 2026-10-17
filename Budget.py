from datetime import datetime
from decimal import Decimal
from pathlib import Path
from Transaction import check_amount
from Load_data import load_data
from Save_data import save_data, initialize, FIELDS


def check_month(month: str) -> str:
    if len(month) != 7:
        raise ValueError("월은 YYYY-MM 형식으로 입력하세요.")
    parsed = datetime.strptime(month, "%Y-%m")
    if parsed.date().isoformat()[:7] != month:
        raise ValueError("월은 YYYY-MM 형식으로 입력하세요.")
    return month


class Budget:
    def __init__(self, data_dir: str | Path = "data") -> None:
        folder = initialize(data_dir)
        self.path = folder / "budgets.csv"

    def edit_budget(self, new_budget_amount: str | int | Decimal, date: str) -> None:
        check_month(date)
        amount = check_amount(new_budget_amount)
        rows = list(load_data(self.path))
        for row in rows:
            if row["날짜"] == date:
                row["예산액"] = str(int(amount))
                save_data(self.path, rows, FIELDS["budgets"])
                return
        rows.append({"예산액": str(int(amount)), "날짜": date})
        save_data(self.path, rows, FIELDS["budgets"])

    def get_budget(self, date: str) -> Decimal | None:
        for row in load_data(self.path):
            if row["날짜"] == date:
                return check_amount(row["예산액"])
        return None
