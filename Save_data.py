# CSV 파일 저장
import csv
from pathlib import Path

FIELDS = {
    "transactions": ["type", "money", "category", "date", "memo", "tag", "id"],
    "categories": ["name"],
    "budgets": ["날짜", "예산액"],
}


def save_data(path, rows, fields):
    path = Path(path)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    # 저장을 끝낸 뒤 교체하여 기존 파일을 보호합니다.
    temporary.replace(path)


def initialize(data_dir="data"):
    folder = Path(data_dir)
    folder.mkdir(parents=True, exist_ok=True)
    for name, fields in FIELDS.items():
        path = folder / (name + ".csv")
        if not path.exists() or path.stat().st_size == 0:
            save_data(path, [], fields)
    return folder
