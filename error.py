import argparse


class InputError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError(message + " (해결: --help로 입력 형식을 확인하세요.)")


def print_error(error):
    import sys
    print(f"오류: {error}\n해결 힌트: 입력값, 데이터 파일 형식과 폴더 권한을 확인하세요.", file=sys.stderr)
