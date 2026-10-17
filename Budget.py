from datetime import datetime
from Transaction import check_amount


def check_month(month):
    if len(month) != 7:
        raise ValueError("월은 YYYY-MM 형식으로 입력하세요.")
    datetime.strptime(month, "%Y-%m")
    return month


class Budget:
    def __init__(self):
        self.budget = []

    def edit_budget(self, new_budget_amount, date):
        check_month(date)
        amount = check_amount(new_budget_amount)
        for row in self.budget:
            if row["날짜"] == date:
                row["예산액"] = amount
                return
        self.budget.append({"예산액": amount, "날짜": date})

    def get_budget(self, date):
        for row in self.budget:
            if row["날짜"] == date:
                return row["예산액"]
        return None

# 마지막 단계: 예산 데이터를 파일로 저장하고 불러옵니다.
