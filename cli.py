#!/usr/bin/env python3
"""
Vibe Compiler CLI

Usage:
  python cli.py compile <file_or_script>
  python cli.py run <file_or_script>

Arguments:
  file_or_script: Either a path to a .vibe file, or a semicolon-delimited script
"""

import argparse
import os
import tempfile

from src.compile import compile
from src.llm import set_debug_file
from src.run import run_vibe


def is_file_path(input_str: str) -> bool:
    """Check if input string is a file path (contains . or /) vs inline script."""
    return "." in input_str or "/" in input_str or "\\" in input_str


def parse_inline_script(script: str) -> str:
    """Convert semicolon-delimited script to multiline format."""
    lines = [line.strip() for line in script.split(";") if line.strip()]
    return "\n".join(lines)


def compile_mode(input_arg: str):
    """Compile a vibe program and print the AST."""
    if is_file_path(input_arg):
        # Input is a file path
        if not os.path.exists(input_arg):
            print(f"Error: File '{input_arg}' not found")
            return 1

        program = compile(input_arg)
        print(f"Compiled '{input_arg}':")
        print(program)
    else:
        # Input is an inline script
        script_content = parse_inline_script(input_arg)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vibe", delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            program = compile(temp_file)
            print("Compiled inline script:")
            print(f"Script: {script_content}")
            print("AST:")
            print(program)
        finally:
            # Clean up temp file
            os.unlink(temp_file)

    return 0


def run_mode(input_arg: str):
    """Run a vibe program and print the result."""
    if is_file_path(input_arg):
        # Input is a file path
        if not os.path.exists(input_arg):
            print(f"Error: File '{input_arg}' not found")
            return 1

        print(f"Running '{input_arg}'...")
        result = run_vibe(input_arg)
        print("Final result:")
        print(result)
    else:
        # Input is an inline script
        script_content = parse_inline_script(input_arg)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vibe", delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            print(f"Running inline script: {script_content}")
            result = run_vibe(temp_file)
            print("Final result:")
            print(result)
        finally:
            # Clean up temp file
            os.unlink(temp_file)

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Vibe Compiler - compile and run vibe programs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py compile vibes/example.vibe
  python cli.py run vibes/example.vibe
  python cli.py compile "for each item in list; process item; combine results"
  python cli.py run "for each item in list; process item; combine results"
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
        "--debug",
        action="store_true",
        help="Enable debug logging of all LLM messages to debug.log",
    )

    args = parser.parse_args()

    # Enable debug logging if requested
    if args.debug:
        set_debug_file("debug.log")
        print("Debug logging enabled: writing to debug.log")

    try:
        if args.mode == "compile":
            return compile_mode(args.input)
        elif args.mode == "run":
            return run_mode(args.input)
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
