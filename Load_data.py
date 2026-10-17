# CSV 파일을 한 줄씩 읽습니다.
import csv
from pathlib import Path
from Save_data import FIELDS


def load_data(path):
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        if reader.fieldnames != FIELDS[path.stem]:
            raise ValueError(f"{path}: CSV 열 이름이 올바르지 않습니다. 파일의 첫 줄을 확인하세요.")
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f"{path}: CSV 항목 수가 올바르지 않습니다. {reader.line_num}번째 줄을 확인하세요.")
            yield row
