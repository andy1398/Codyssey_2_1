import argparse
import csv
import sys
from collections.abc import Callable
from decimal import InvalidOperation
from functools import wraps
from typing import ParamSpec

P = ParamSpec("P")  # 감싸는 함수의 매개변수 타입을 그대로 유지합니다.


class InputError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InputError(message + " (해결: --help로 입력 형식을 확인하세요.)")


def print_error(error: Exception) -> None:
    print(f"오류: {error}\n해결 힌트: 입력값, 데이터 파일 형식과 폴더 권한을 확인하세요.", file=sys.stderr)


def handle_errors(function: Callable[P, int]) -> Callable[P, int]:
    """명령에서 발생한 오류를 메시지와 종료 코드로 바꾸는 데코레이터."""
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
        try:
            return function(*args, **kwargs)
        except (InputError, ValueError, OSError, KeyError, TypeError,
                InvalidOperation, csv.Error) as error:
            print_error(error)
            return 1
        except (EOFError, KeyboardInterrupt):
            print("\n오류: 입력이 취소되었습니다. 명령을 다시 실행하세요.", file=sys.stderr)
            return 1
    return wrapper
