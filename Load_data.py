# CSV 파일을 한 줄씩 읽습니다.
import csv
from collections.abc import Iterator
from pathlib import Path
from Save_data import FIELDS


def load_data(path: str | Path) -> Iterator[dict[str, str]]:
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        old_fields = ["type", "money", "category", "date", "memo", "tag", "id"]
        old_format = path.stem == "transactions" and reader.fieldnames == old_fields
        if reader.fieldnames != FIELDS[path.stem] and not old_format:
            raise ValueError(f"{path}: CSV 열 이름이 올바르지 않습니다. 파일의 첫 줄을 확인하세요.")
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f"{path}: CSV 항목 수가 올바르지 않습니다. {reader.line_num}번째 줄을 확인하세요.")
            # 예전 저장 파일도 읽습니다. 다음 저장부터 새 열 이름을 사용합니다.
            if old_format:
                row["amount"] = row.pop("money")
                row["tags"] = row.pop("tag")
            yield row
