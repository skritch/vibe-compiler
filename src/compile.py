import json

from tqdm import tqdm

from src.llm import LLM
from src.program import Command, Map, Program, Reduce, Statement
from src.prompts import (
    COMPILER_SYSTEM_PROMPT,
    classification_prompt,
    require_json_list_prompt,
    retry_classification_prompt,
)
from src.schemas import CLASSIFICATION_SCHEMA


def compile(lines: list[str]) -> Program:
    """
    Compile a vibe into an program.

    Algorithm:
    1. Read file line by line
    2. For each non-empty line:
       a. Ask LLM: "What type of statement is this? (map/reduce/command)"
       b. Generate the AST node JSON for the line.
       c. Parse JSON response into appropriate AST node
    3. Return Program of all top-level statements
    """

    llm = LLM.from_env()
    conversation = llm.converse(COMPILER_SYSTEM_PROMPT)

    statements: list[Statement] = []
    map_stack: list[Map] = []  # Stack to track nested map statements

    # Filter out empty lines for progress tracking
    non_empty_lines = [
        (i + 1, line.strip()) for i, line in enumerate(lines) if line.strip()
    ]

    for line_num, line in tqdm(
        non_empty_lines, desc="Compiling lines", unit="line", ncols=0
    ):
        # Step 1: Classify the line type and get tools in one call

        classification_response = conversation.chat(
            classification_prompt(line), response_schema=CLASSIFICATION_SCHEMA
        )

        try:
            classification_data = json.loads(classification_response)
            line_type = classification_data["type"]
            tools = classification_data["tools"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(
                f"Failed to parse classification response at line {line_num}: {e}"
            )

        # Step 2: Generate AST node based on type and handle nesting
        if line_type == "map":
            # Create new map and push to stack
            new_map = _parse_map_line(line, tools)
            map_stack.append(new_map)

        elif line_type == "command":
            command = _parse_command_line(line, tools)

            # If we're inside a map, add to its body, otherwise add to main statements
            if map_stack:
                current_map = map_stack[-1]
                current_map.body.statements.append(command)
            else:
                statements.append(command)

        elif line_type == "reduce":
            # Check if we have any maps to reduce
            if not map_stack:
                # Try to correct the LLM's classification
                retry_response = conversation.chat(
                    retry_classification_prompt(line),
                    response_schema=CLASSIFICATION_SCHEMA,
                )

                try:
                    retry_data = json.loads(retry_response)
                    line_type = retry_data["type"]
                    tools = retry_data["tools"]

                    # If it's still reduce, crash
                    if line_type == "reduce":
                        raise ValueError(
                            f"Line {line_num}: Invalid reduce operation - no maps to reduce from. "
                            f"Line: '{line}'"
                        )

                    # Recursively handle the corrected classification
                    if line_type == "map":
                        new_map = _parse_map_line(line, tools)
                        map_stack.append(new_map)
                    elif line_type == "command":
                        command = _parse_command_line(line, tools)
                        statements.append(command)

                except (json.JSONDecodeError, KeyError) as e:
                    raise ValueError(
                        f"Failed to parse retry classification at line {line_num}: {e}"
                    )
            else:
                # TODO: currently every map has to have a reduce
                # if we want to nest maps without reducing the inner ones,
                # we will have to do somethig truly silly.

                # Normal reduce operation - finalize maps
                reduce = _parse_reduce_line(line)

                # Finalize the open map and add it to statements.
                completed_map = map_stack.pop()
                completed_map.reduce = reduce
                statements.append(completed_map)

        else:
            raise ValueError(f"Unknown line type '{line_type}' at line {line_num}")

    # Finalize any remaining maps at end of file
    while map_stack:
        completed_map = map_stack.pop()
        statements.append(completed_map)

    return Program(statements=statements)


def _parse_map_line(line: str, tools: list[str]) -> Map:
    """Parse a map line into a Map AST node."""
    # Augment the prompt to request JSON list format
    augmented_prompt = require_json_list_prompt(line)
    dimension_command = Command(prompt=augmented_prompt, tools=tools)
    return Map(dimension=dimension_command, body=Program(statements=[]), reduce=None)


def _parse_reduce_line(line: str) -> Reduce:
    """Parse a reduce line into a Reduce AST node."""
    return Reduce(prompt=line)


def _parse_command_line(line: str, tools: list[str]) -> Command:
    """Parse a command line into a Command AST node."""
    return Command(prompt=line, tools=tools)
