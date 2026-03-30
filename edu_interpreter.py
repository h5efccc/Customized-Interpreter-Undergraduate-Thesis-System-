import sys

from pnc_lang.runner import run_file


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python edu_interpreter.py <program.pnc>")
        return 2
    return run_file(argv[1])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

