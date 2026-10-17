# 2단계: 메모리에서 거래, 검색, 요약, 카테고리를 관리합니다.
# 파일 저장과 로드는 마지막 단계에서 연결합니다.
from decimal import Decimal
from Transaction import Transaction, check_date
from Budget import Budget, check_month


class TransactionControl:
    def __init__(self):
        self.transactions = []
        self.categories = []
        self.budget = Budget()

    def sort_transactions(self):
        self.transactions.sort(key=lambda row: row["date"], reverse=True)

    def check_category(self, name):
        if name not in self.categories:
            raise ValueError("등록되지 않은 카테고리입니다. category add로 먼저 추가하세요.")

    def add_transaction(self, transaction):
        self.check_category(transaction.category)
        rows = self.transactions.copy()
        rows.insert(0, transaction.to_dict())
        self.transactions = rows
        self.sort_transactions()
        return transaction.id

    def show_transactions(self, limit=10):
        if limit <= 0:
            raise ValueError("limit은 1 이상으로 입력하세요.")
        for index, row in enumerate(self.transactions):
            if index >= limit:
                break
            yield row

    def delete_transaction(self, transaction_id):
        rows = self.transactions.copy()
        remaining = [row for row in rows if row["id"] != transaction_id]
        if len(rows) == len(remaining):
            raise ValueError("거래 ID를 찾을 수 없습니다. list로 ID를 확인하세요.")
        self.transactions = remaining

    def update_transaction(self, transaction_id, changes):
        rows = self.transactions.copy()
        for index, row in enumerate(rows):
            if row["id"] == transaction_id:
                row = row.copy()
                row.update(changes)
                transaction = Transaction(**row)
                self.check_category(transaction.category)
                rows[index] = transaction.to_dict()
                self.transactions = rows
                self.sort_transactions()
                return
        raise ValueError("거래 ID를 찾을 수 없습니다. list로 ID를 확인하세요.")

    def search_transactions(self, start=None, end=None, category=None, type=None, q=None, tag=None):
        if start:
            check_date(start)
        if end:
            check_date(end)
        if start and end and start > end:
            raise ValueError("시작 날짜는 종료 날짜보다 늦을 수 없습니다.")
        for row in self.transactions:
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
            if tag and tag not in [value.strip() for value in row["tag"].split(",")]:
                continue
            yield row

    def summarize_transactions(self, date, top=5):
        check_month(date)
        if top <= 0:
            raise ValueError("top은 1 이상으로 입력하세요.")
        income = Decimal("0")
        expense = Decimal("0")
        categories = {}
        count = 0
        for row in self.transactions:
            if row["date"][:7] != date:
                continue
            count += 1
            amount = Decimal(row["money"])
            if row["type"] == "income":
                income += amount
            else:
                expense += amount
                name = row["category"]
                categories[name] = categories.get(name, Decimal("0")) + amount
        if count == 0:
            print("데이터 없음")
        print(f"총 수입: {income}\n총 지출: {expense}\n잔액: {income - expense}")
        for name, amount in sorted(categories.items(), key=lambda item: item[1], reverse=True)[:top]:
            print(f"{name}: {amount}")
        budget = self.budget.get_budget(date)
        if budget is not None:
            print(f"예산: {budget}, 사용률: {expense / budget * 100:.2f}%")
            if expense > budget:
                print("경고: 예산을 초과했습니다.")

    def category(self, action, name=None):
        if action == "list":
            if not self.categories:
                print("등록된 카테고리가 없습니다. category add로 추가하세요.")
            for item in self.categories:
                print(item)
            return
        if not name or not name.strip():
            raise ValueError("카테고리 이름을 입력하세요.")
        if action == "add":
            if name in self.categories:
                raise ValueError("이미 등록된 카테고리입니다.")
            self.categories.append(name)
        elif action == "remove":
            self.check_category(name)
            if any(row["category"] == name for row in self.transactions):
                raise ValueError("사용 중인 카테고리입니다. 거래를 수정하거나 삭제한 뒤 다시 시도하세요.")
            self.categories.remove(name)
        else:
            raise ValueError("카테고리 명령은 add, list, remove 중 하나를 입력하세요.")


Transaction_Control = TransactionControl
