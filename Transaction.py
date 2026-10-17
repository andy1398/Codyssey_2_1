from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4


def check_date(value):
    if len(value) != 10:
        raise ValueError("날짜는 YYYY-MM-DD 형식으로 입력하세요.")
    datetime.strptime(value, "%Y-%m-%d")
    return value


def check_amount(value):
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("금액은 숫자로 입력하세요.")
    if not amount.is_finite() or amount <= 0:
        raise ValueError("금액은 0보다 큰 유한한 숫자로 입력하세요.")
    return amount


class Transaction:
    def __init__(self, type, money, category, date, memo="", tag=None, id=None):
        if type not in ["income", "expense"]:
            raise ValueError("타입은 income(수입), expense(지출) 중 하나를 입력하세요.")
        self.type = type
        self.money = str(check_amount(money))
        self.category = category
        self.date = check_date(date)
        self.memo = memo
        self.tag = tag or ""
        self.id = id or uuid4().hex[:12]

    def to_dict(self):
        return vars(self).copy()
