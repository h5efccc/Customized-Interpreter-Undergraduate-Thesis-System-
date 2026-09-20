import sys

from pnc_lang.gui import launch_gui, launch_gui_with_file
from pnc_lang.runner import run_file


def main(argv: list[str]) -> int:
    args = argv[1:]
    run_execution = False
    use_cli = False

    if "--execute" in args:
        run_execution = True
        args.remove("--execute")

    if "--cli" in args:
        use_cli = True
        args.remove("--cli")

    # GUI mode (default)
    if not use_cli:
        if len(args) == 0:
            launch_gui()
            return 0
        if len(args) == 1:
            launch_gui_with_file(args[0])
            return 0
        print("Usage: python edu_interpreter.py [program.pnc]")
        print("       python edu_interpreter.py --cli [--execute] <program.pnc>")
        return 2

    # CLI mode
    if len(args) != 1:
        print("Usage: python edu_interpreter.py --cli [--execute] <program.pnc>")
        return 2

    return run_file(args[0], run_execution=run_execution)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
