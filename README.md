# 용돈 기입장

Python 3.10 이상의 표준 라이브러리만 사용하는 CSV 기반 콘솔 가계부입니다.
기존 파일 구성, Transaction / TransactionControl / Budget 클래스를 유지했습니다. 거래 필드는 과제에 맞게 amount와 tags를 사용합니다.

## 실행 방법

이 파일이 있는 폴더에서 실행합니다. 별도 설치는 필요하지 않습니다.

```sh
python3 Main.py
```

명령 입력 창에서 `add`, `list`, `--help` 등을 입력합니다. `exit` 또는 `quit`으로 종료합니다.
명령 하나만 실행할 수도 있습니다.

```sh
python3 Main.py --help
python3 Main.py list --limit 10
python3 Main.py --data-dir ./my_data list --limit 10
```

`--data-dir`는 명령 앞에 지정합니다. 모든 명령과 하위 명령에서 `--help`를 지원합니다.
옵션은 과제의 상세 요구사항과 예시에 따라 `--`로 통일했습니다.
`python -m budget_app`은 권장 예시이므로 기존 `Main.py` 실행 구조를 유지했습니다.

## 사용 순서

처음에는 등록된 카테고리가 없습니다. 카테고리를 먼저 추가하세요.

```sh
python3 Main.py category add
# 카테고리명: food
python3 Main.py category add salary
python3 Main.py category list
python3 Main.py add
```

`add`는 날짜, 타입, 카테고리, 금액, 메모, 태그를 차례로 입력받습니다.
메모와 태그는 엔터로 생략할 수 있습니다. 잘못 입력하면 원인과 힌트를 출력하며 저장하지 않습니다.
날짜는 YYYY-MM-DD, 타입은 income 또는 expense, 금액은 양수 정수입니다.
카테고리는 등록된 이름을 사용합니다. 저장 후 생성된 거래 ID를 출력합니다.
기존 옵션 방식도 유지합니다. 필수 네 옵션을 모두 주면 추가 입력 없이 실행합니다.

```sh
python3 Main.py add --date 2026-10-02 --type expense --category food --amount 8000 --memo "점심" --tags "식사,학교"
python3 Main.py list --limit 10
python3 Main.py search --from 2026-10-01 --to 2026-10-31 --category food --type expense --q 점심 --tag 학교
python3 Main.py budget set --month 2026-10 --amount 50000
python3 Main.py summary --month 2026-10 --top 5
python3 Main.py update --id 거래ID --amount 9000
python3 Main.py delete --id 거래ID
python3 Main.py category remove salary
```

- `list`: 기본 10건, 최신 거래 날짜순. 같은 날짜는 나중에 추가한 거래가 먼저 나옵니다.
- `search`: 지정한 조건을 모두 만족하는 거래. 날짜 양 끝 포함, 메모는 대소문자 구분 없는 부분 검색, 태그는 정확히 일치하는 항목 검색입니다.
- `update`: **옵션 방식으로 고정**합니다. `--id`와 수정할 옵션 하나 이상을 지정합니다. `--memo ""`, `--tags ""`로 내용을 지울 수 있습니다.
- `delete` / `update`: 없는 ID는 오류로 처리합니다.
- `summary`: 월별 수입, 지출, 잔액, 지출 카테고리 TOP N을 출력합니다. `--top` 기본값은 5입니다. 거래가 없으면 데이터 없음을 알립니다.
- `budget`: 월 예산을 저장합니다. 예산 조회는 해당 월의 `summary`에서 하며 사용률과 초과 경고를 표시합니다.
- `category`: 사용 중인 카테고리는 삭제할 수 없습니다. `add` / `remove`에서 이름을 생략하면 입력받습니다.

## 저장 파일과 안전성

기본 폴더는 `./data`이며 첫 실행 시 다음 UTF-8 CSV 파일을 자동 생성합니다.

| 파일 | 열 이름 |
| --- | --- |
| transactions.csv | type,amount,category,date,memo,tags,id |
| categories.csv | name |
| budgets.csv | 날짜,예산액 |

예전 money/tag 열 이름으로 저장된 거래 파일도 읽을 수 있습니다.
다음 거래 저장이 성공하면 amount/tags 열 이름으로 교체합니다. 조회만으로 파일을 바꾸지 않습니다.
기존 데이터에 소수 금액이 있다면 새 정수 검증 정책에 맞게 정리해야 합니다.

조회·검색·월별 요약은 `load_data()`와 `load_transactions()`의 `yield`로 한 줄씩 처리합니다.
읽은 거래의 날짜, 타입, 양수 정수 금액, 카테고리와 빈 ID를 확인합니다.
잘못된 거래를 발견하면 오류를 출력하고 종료 코드 1을 반환합니다. 쓰기 중 발견하면 원본을 유지합니다.
목록은 --limit까지 읽은 거래만 검증하므로 파일 전체 검사 기능은 아닙니다.
빈 검색 날짜(`--from ""`, `--to ""`)도 오류로 처리합니다.
최신순 조회를 위해 **추가·수정·삭제 시 전체 거래를 메모리에 읽고 정렬하여 저장**합니다.
조회에는 전체 로드가 없지만, 쓰기 작업은 전체 거래 수에 비례하는 메모리가 필요합니다.

저장할 때는 같은 폴더의 임시 파일에 먼저 쓰고, 성공한 경우 원본을 교체합니다.
쓰기 도중 실패하면 원본을 유지하고 임시 파일을 정리합니다.
동시에 여러 프로그램을 실행하여 같은 저장 폴더를 수정하는 용도는 지원하지 않습니다.

## CSV 가져오기 / 내보내기

```sh
python3 Main.py export --out export.csv --month 2026-10
python3 Main.py export --out export.csv --from 2026-10-01 --to 2026-10-31
python3 Main.py import --from import.csv
```

내보내기는 `--month` 또는 `--from`과 `--to` 한 쌍이 필수이며 둘을 동시에 사용할 수 없습니다.
출력 폴더는 미리 생성해야 합니다. 이미 존재하는 출력 파일은 교체하지만 세 내부 저장 파일은 덮어쓸 수 없습니다.
결과가 없으면 헤더만 있는 CSV를 생성하고 0건을 출력합니다.

공통 형식은 UTF-8, 헤더 포함입니다.

| 열 | 필수 | 내용 |
| --- | --- | --- |
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표로 구분한 문자열 |

```csv
date,type,category,amount,memo,tags
2026-10-02,expense,food,8000,점심,"식사,학교"
2026-10-03,income,salary,100000,용돈,
```

태그처럼 쉼표가 들어가는 값은 큰따옴표로 감쌉니다. 내보내기는 `csv` 모듈이 자동 처리합니다.
가져올 때 memo/tags 열은 생략할 수 있습니다. 알 수 없는 열과 중복 헤더는 오류로 처리합니다.
**모든 행의 검증이 성공해야 한 번에 반영**합니다. 잘못된 행이 있으면 전체 가져오기를 취소합니다.
각 거래에는 새 ID를 부여합니다. 같은 파일을 다시 가져오면 거래가 다시 추가됩니다.
처리 후 가져온/내보낸 건수를 출력합니다.

## 파일별 역할

| 파일 | 역할 |
| --- | --- |
| Main.py | 명령어 파싱, 대화형 입력, 명령 실행 및 결과 출력 |
| Transaction.py | 거래 객체, 날짜·타입·금액 검증 |
| Transaction_Control.py | 거래 검증·CRUD, 검색·요약, 카테고리, import/export |
| Budget.py | 월별 예산 저장·조회와 월 검증 |
| Load_data.py | 제너레이터 기반 CSV 읽기 |
| Save_data.py | 파일 초기화, 임시 파일 저장 및 교체 |
| error.py | 오류 출력, argparse 오류 변환, 예외 처리 데코레이터 |
| test_budget_app.py | 표준 unittest 기반 기능·데이터 보호 테스트 |

확장자가 없는 기존 `Transaction_Control` 파일은 실제 구현을 불러오는 안내용 파일로 남겼습니다.
`Transaction`은 필드와 생성자를 직접 정의한 데이터 모델입니다. 클래스 구조를 유지하려고 dataclass로 바꾸지 않았습니다.

타입 힌트 예: `show_transactions(limit: int) -> Iterator[dict[str, str]]`는 정수 제한을 받고 거래 딕셔너리를 하나씩 내보낸다는 계약입니다.
타입 힌트 자체가 실행 중 검증을 수행하지는 않으므로 입력 검증 함수도 사용합니다.
`@handle_errors`는 `main()`의 예외 처리 코드를 분리한 데코레이터입니다.
`functools.wraps`는 원래 함수 정보를 보존하며, `ParamSpec`은 감싸는 함수의 매개변수 타입을 유지합니다.

정상 명령은 종료 코드 0, 오류는 1을 반환합니다. 예상 가능한 입력·파일 오류는 스택트레이스 없이 원인과 힌트를 출력합니다.
대화형 셸에서는 오류 후 다시 명령을 입력할 수 있고, 종료 시 마지막 명령의 코드를 반환합니다.

## 테스트

```sh
python3 -m unittest -v test_budget_app.py
```

임시 폴더를 사용하므로 실제 `data` 폴더는 변경하지 않습니다.

요약과 카테고리 메서드는 출력할 문자열 목록을 반환하고, Main.py가 for문과 print로 화면에 표시합니다.
