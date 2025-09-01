#!/usr/bin/env python
import argparse
import os

from src.compile import compile
from src.llm import set_log_file
from src.program import Program
from src.run import run_program

LOG_DIR = os.getenv("LOG_DIR", ".data/")

def create_log_file(input_name: str, mode: str) -> str:

    if '.' in input_name and os.path.exists(input_name):
        # Remove extension and get base name
        base_name = os.path.splitext(os.path.basename(input_name))[0]
        filename = os.path.join(LOG_DIR, f"{base_name}-{mode}.log")
    else:
        filename = os.path.join(LOG_DIR, "script.log")

    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    set_log_file(filename)
    return filename

def handle_input(input_arg: str, is_script: bool):
    if is_script:
        return [line.strip() for line in input_arg.split(";") if line.strip()]

    if not os.path.exists(input_arg):
        raise ValueError(f"Error: File '{input_arg}' not found")

    with open(input_arg) as f:
        lines = f.readlines()
    return lines

def parse_inline_script(script: str) -> list[str]:
    """Convert semicolon-delimited script to multiline format."""
    return [line.strip() for line in script.split(";") if line.strip()]


def compile_mode(input_arg: str, is_script: bool, pretty: bool = False):
    """Compile a vibe program and print the AST."""

    program = compile(handle_input(input_arg, is_script))
    output = str(program) if pretty else program.model_dump_json(indent=2)

    if pretty:
        output = str(output)
    return output


def run_mode(input_arg: str, is_script: bool, compiled: bool = False):
    """Run a vibe program and print the result."""

    if compiled:
        with open(input_arg) as f:
            json_content = f.read()
        program = Program.model_validate_json(json_content)
    else:
        program = compile(handle_input(input_arg, is_script))

    result = run_program(program)
    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Vibe Compiler - compile and run vibe programs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py compile vibes/example.vibe -o vibes/examples.vibec
  python cli.py run vibes/example.vibe
  python cli.py run -c vibes/example.vibec
  python cli.py compile -s "for each item in list; process item; combine results"
  python cli.py run -s "for each item in list; process item; combine results"
        """,
    )

    parser.add_argument(
        "mode",
        choices=["compile", "run"],
        help="Mode: compile (show AST) or run (execute program)",
    )

    parser.add_argument(
        "input", help="Either a path to a .vibe file or a semicolon-delimited script"
    )

    parser.add_argument(
        "-c",
        "--compiled",
        action="store_true",
        help="Run mode only: treat input as a compiled .vibec file (JSON format)",
    )

    parser.add_argument(
        "-s", "--script",
        action="store_true",
        help='Interpret "input" as a script instead of a filename'
    )

    parser.add_argument("-o", "--output", help="Output file (defaults to stdout)")

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Compile mode only: output string representation instead of JSON",
    )

    args = parser.parse_args()

    # Enable debug logging if requested
    log_file = create_log_file(
        args.input,
        args.mode
    )

    # Validate arguments
    if args.compiled and args.mode != "run":
        print("Error: -c/--compiled flag can only be used with 'run' mode")
        return 1

    if args.compiled and args.script:
        print("Error: -c/--compiled flag cannot be used with -s/--script flag")
        return 1

    if args.pretty and args.mode != "compile":
        print("Error: --pretty flag can only be used with 'compile' mode")
        return 1

    if args.mode == "compile":
        output = compile_mode(args.input, is_script=args.script, pretty=args.pretty)
    elif args.mode == "run":
        output = run_mode(args.input, is_script=args.script, compiled=args.compiled)

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    exit(main())
