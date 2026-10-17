# 용돈 기입장

간단한 문법으로 단계별 구현합니다.

1. 거래 객체와 입력값 검사
2. 메모리에서 거래 추가·조회·수정·삭제·검색, 카테고리 관리, 월별 요약, 예산 관리
3. CSV 저장·로드와 파일 스트리밍 연결

CSV 저장·로드까지 연결했습니다. 변경 사항은 자동 저장되고 재실행 후에도 유지됩니다.

```sh
python3 Main.py
```

실행 후 아래 명령을 차례로 입력할 수 있습니다.

```text
category add food
category list
add --date 2026-10-02 --type expense --category food --amount 8000 --memo "점심" --tags "식사,학교"
list --limit 10
search --from 2026-10-01 --to 2026-10-31 --tag 학교
budget set --month 2026-10 --amount 50000
summary --month 2026-10 --top 5
update --id 거래ID --amount 9000
delete --id 거래ID
category add salary
category remove salary
--help
exit
```

거래ID는 list에 표시된 실제 ID로 바꿉니다.
타입은 income(수입), expense(지출)입니다.
금액과 예산은 0보다 큰 숫자입니다.
카테고리는 빈 목록에서 시작합니다. category add로 먼저 추가한 뒤 거래에 사용합니다.
사용 중인 카테고리는 삭제할 수 없습니다.

파이썬에서 불러오는 구현 파일은 Transaction_Control.py입니다.
기존 Transaction_Control 파일에도 같은 구현 내용을 남겨두었습니다.

기본 저장 폴더는 ./data입니다. 첫 실행 시 다음 세 파일을 자동 생성합니다.

- transactions.csv: 거래
- categories.csv: 직접 추가한 카테고리
- budgets.csv: 월별 예산

카테고리를 자동으로 추가하지 않습니다. 빈 상태에서는 category add를 먼저 사용하세요.
저장 폴더를 바꾸려면 프로그램을 실행할 때 지정합니다.

```sh
python3 Main.py --data-dir ./my_data
python3 Main.py --data-dir ./my_data category add 식비
python3 Main.py --data-dir ./my_data list --limit 10
```

거래는 저장할 때 최신 날짜순으로 정렬합니다. 같은 날짜는 새 거래가 먼저 나옵니다.
조회와 검색은 제너레이터로 CSV를 한 줄씩 읽습니다.
거래 추가·수정·삭제 시에는 기존 거래를 읽어서 정렬 후 다시 저장합니다.
CSV 열 이름이나 항목 수가 잘못되면 파일 위치와 오류 원인을 출력합니다.
