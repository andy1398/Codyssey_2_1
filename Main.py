import csv
import sys
import shlex
from decimal import InvalidOperation
from Transaction import Transaction
from Transaction_Control import TransactionControl
from error import Parser, InputError, print_error


def make_parser():
    parser = Parser(description="용돈 기입장")
    parser.add_argument("--data-dir", "-data-dir", default="data")
    commands = parser.add_subparsers(dest="command")
    for name in ["add", "update"]:
        command = commands.add_parser(name)
        if name == "update":
            command.add_argument("--id", required=True)
        for field in ["date", "type", "category", "amount"]:
            options = {"required": name == "add"}
            if field == "type":
                options["choices"] = ["income", "expense"]
            command.add_argument("--" + field, **options)
        command.add_argument("--memo")
        command.add_argument("--tags", help="쉼표로 구분한 태그")
    command = commands.add_parser("delete")
    command.add_argument("--id", required=True)
    command = commands.add_parser("list")
    command.add_argument("--limit", type=int, default=10)
    command = commands.add_parser("search")
    command.add_argument("--from", dest="start")
    command.add_argument("--to", dest="end")
    command.add_argument("--category")
    command.add_argument("--type", choices=["income", "expense"])
    command.add_argument("--q")
    command.add_argument("--tag")
    command = commands.add_parser("summary")
    command.add_argument("--month", required=True)
    command.add_argument("--top", "-top", type=int, default=5)
    command = commands.add_parser("budget")
    actions = command.add_subparsers(dest="action", required=True)
    command = actions.add_parser("set")
    command.add_argument("--month", required=True)
    command.add_argument("--amount", required=True)
    command = commands.add_parser("category")
    actions = command.add_subparsers(dest="action", required=True)
    for action in ["add", "list", "remove"]:
        command = actions.add_parser(action)
        if action != "list":
            command.add_argument("name", nargs="?")
            command.add_argument("--name", dest="option_name")
    return parser


def print_transactions(rows):
    found = False
    for row in rows:
        found = True
        print(f"{row['id']} | {row['date']} | {row['type']} | {row['money']} | "
              f"{row['category']} | {row['memo']} | {row['tag']}")
    if not found:
        print("데이터 없음")


def main(argv=None, control=None):
    try:
        args = make_parser().parse_args(argv)
        if args.command is None:
            if control is not None:
                raise ValueError("명령을 입력하세요. --help로 명령 목록을 확인하세요.")
            return interactive(args.data_dir)
        if control is None:
            control = TransactionControl(args.data_dir)
        if args.command == "add":
            transaction = Transaction(args.type, args.amount, args.category, args.date,
                                      args.memo or "", args.tags or "")
            print("추가 완료. ID:", control.add_transaction(transaction))
        elif args.command == "update":
            changes = {}
            for option, field in [("date", "date"), ("type", "type"), ("category", "category"),
                                  ("amount", "money"), ("memo", "memo"), ("tags", "tag")]:
                value = getattr(args, option)
                if value is not None:
                    changes[field] = value
            if not changes:
                raise ValueError("수정할 항목을 하나 이상 입력하세요.")
            control.update_transaction(args.id, changes)
            print("수정 완료")
        elif args.command == "delete":
            control.delete_transaction(args.id)
            print("삭제 완료")
        elif args.command == "list":
            print_transactions(control.show_transactions(args.limit))
        elif args.command == "search":
            print_transactions(control.search_transactions(args.start, args.end, args.category,
                                                          args.type, args.q, args.tag))
        elif args.command == "summary":
            control.summarize_transactions(args.month, args.top)
        elif args.command == "budget":
            control.budget.edit_budget(args.amount, args.month)
            print("예산 설정 완료")
        elif args.command == "category":
            control.category(args.action, getattr(args, "option_name", None) or getattr(args, "name", None))
        return 0
    except (InputError, ValueError, OSError, KeyError, TypeError, InvalidOperation, csv.Error) as error:
        print_error(error)
        return 1


def interactive(data_dir="data"):
    control = TransactionControl(data_dir)
    print("[ 용돈 기입장 ]")
    print("명령어 안내: --help / 종료: exit")
    print(f"저장 폴더: {data_dir} (변경 사항은 자동 저장됩니다.)")
    while True:
        try:
            command = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if command in ["exit", "quit"]:
            return 0
        if not command:
            continue
        try:
            arguments = shlex.split(command)
        except ValueError as error:
            print_error(error)
            continue
        try:
            if any(value.split("=")[0] in ["--data-dir", "-data-dir"] for value in arguments):
                raise ValueError("저장 폴더는 실행할 때 지정하세요: python3 Main.py --data-dir 폴더")
            if not arguments:
                continue
            if main(arguments, control) != 0:
                continue
        except ValueError as error:
            print_error(error)
        except SystemExit as error:
            # --help를 출력한 뒤에도 입력을 계속 받습니다.
            if error.code:
                return error.code


if __name__ == "__main__":
    sys.exit(main())
