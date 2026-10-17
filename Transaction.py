from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4


def check_date(value: str) -> str:
    if len(value) != 10:
        raise ValueError("날짜는 YYYY-MM-DD 형식으로 입력하세요. 예: 2026-10-17")
    parsed = datetime.strptime(value, "%Y-%m-%d")
    if parsed.date().isoformat() != value:
        raise ValueError("날짜는 YYYY-MM-DD 형식으로 입력하세요.")
    return value


def check_amount(value: str | int | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("금액은 양수 정수로 입력하세요. 예: 15000") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("금액은 0보다 큰 유한한 숫자로 입력하세요.")
    if amount != amount.to_integral_value():
        raise ValueError("금액은 소수점 없이 정수로 입력하세요. 예: 15000")
    return amount


class Transaction:
    """거래 한 건의 데이터와 기본 입력 검증을 담당합니다."""

    def __init__(self, type: str, amount: str | int | Decimal, category: str,
                 date: str, memo: str = "", tags: str | None = None,
                 id: str | None = None) -> None:
        if type not in ["income", "expense"]:
            raise ValueError("타입은 income(수입), expense(지출) 중 하나를 입력하세요.")
        self.type = type
        self.amount = str(int(check_amount(amount)))
        self.category = category
        self.date = check_date(date)
        self.memo = memo
        self.tags = tags or ""
        self.id = id or uuid4().hex[:12]

    def to_dict(self) -> dict[str, str]:
        return vars(self).copy()
