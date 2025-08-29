#!/usr/bin/env python
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

from src.compile import compile
from src.llm import set_log_file
from src.program import Program
from src.run import run_program, run_vibe


def is_file_path(input_str: str) -> bool:
    """Check if input string is a file path vs inline script."""
    if input_str.endswith(('.vibe', '.vibec')):
        return True
    if os.path.exists(input_str):
        return True
    return False


def parse_inline_script(script: str) -> list[str]:
    """Convert semicolon-delimited script to multiline format."""
    return [line.strip() for line in script.split(";") if line.strip()]


def compile_mode(input_arg: str, output_file: str | None = None):
    """Compile a vibe program and print the AST."""
    if is_file_path(input_arg):
        # Input is a file path
        if not os.path.exists(input_arg):
            raise ValueError(f"Error: File '{input_arg}' not found")
        
        with open(input_arg) as f:
            lines = f.readlines()
        program = compile(lines)
        output = program.model_dump_json(indent=2)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
        else:
            print(output)
    else:
        # Input is an inline script
        lines = parse_inline_script(input_arg)
        program = compile(lines)
        output = program.model_dump_json(indent=2)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
        else:
            print(output)

    return 0


def run_mode(input_arg: str, compiled: bool = False, output_file: str | None = None):
    """Run a vibe program and print the result."""
    if is_file_path(input_arg):
        if not os.path.exists(input_arg):
            raise ValueError(f"Error: File '{input_arg}' not found")

        if compiled:
            # Load compiled program from JSON file
            with open(input_arg, 'r') as f:
                json_content = f.read()
            
            # Parse JSON back to Program object using Pydantic
            program = Program.model_validate_json(json_content)
            result = run_program(program)
        else:
            with open(input_arg) as f:
                lines = f.readlines()
            result = run_vibe(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)
        else:
            print(result)
    else:
        # Input is an inline script
        lines = parse_inline_script(input_arg)
        if compiled:
            raise ValueError("Cannot use compiled mode (-c) with inline scripts")
        
        result = run_vibe(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)
        else:
            print(result)

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
        "-c", "--compiled",
        action="store_true",
        help="Run mode only: treat input as a compiled .vibec file (JSON format)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file (defaults to stdout)"
    )

    # parser.add_argument(
    #     "--log",
    #     action="store_true"
    #     help="Logs the LLM conversation",
    # )

    args = parser.parse_args()

    # Enable debug logging if requested
    set_log_file("conversation.txt")
    print(f"Logging enabled: writing to {"conversation.txt"}")

    # Validate arguments
    if args.compiled and args.mode != "run":
        print("Error: -c/--compiled flag can only be used with 'run' mode")
        return 1

    if args.mode == "compile":
        return compile_mode(args.input, args.output)
    elif args.mode == "run":
        return run_mode(args.input, args.compiled, args.output)


if __name__ == "__main__":
    exit(main())
