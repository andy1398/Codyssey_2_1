# 용돈 기입장

간단한 문법으로 단계별 구현합니다.

1. 거래 객체와 입력값 검사
2. 메모리에서 거래 추가·조회·수정·삭제·검색, 카테고리 관리, 월별 요약, 예산 관리
3. 마지막 단계에서 CSV 저장·로드와 파일 스트리밍 연결 (아직 구현하지 않음)

현재는 2단계까지 동작합니다. 프로그램을 종료하면 데이터가 사라집니다.

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
