# CSV 파일 저장
import csv
from collections.abc import Iterable
from pathlib import Path
from tempfile import NamedTemporaryFile

FIELDS = {
    "transactions": ["type", "money", "category", "date", "memo", "tag", "id"],
    "categories": ["name"],
    "budgets": ["날짜", "예산액"],
}

# 외부에서 가져오거나 내보내는 CSV는 과제의 열 이름을 사용합니다.
CSV_FIELDS = ["date", "type", "category", "amount", "memo", "tags"]


def save_data(path: str | Path, rows: Iterable[dict[str, str]],
              fields: list[str]) -> None:
    path = Path(path)
    temporary = None
    try:
        # 같은 폴더의 임시 파일에 먼저 씁니다. 실패하면 원본을 유지합니다.
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                dir=path.parent, prefix=path.name + ".",
                                suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def initialize(data_dir: str | Path = "data") -> Path:
    folder = Path(data_dir)
    folder.mkdir(parents=True, exist_ok=True)
    for name, fields in FIELDS.items():
        path = folder / (name + ".csv")
        if not path.exists() or path.stat().st_size == 0:
            save_data(path, [], fields)
    return folder
