import json

from tqdm import tqdm

from src.llm import LLM, Conversation
from src.program import Command, Map, Program, Statement
from src.prompts import (
    COMPILER_SYSTEM_PROMPT,
    classification_prompt,
    require_json_list_prompt,
    retry_classification_prompt,
)
from src.schemas import get_compile_schema


def advance(line: str, statements: list[Statement], map_stack: list[Map], conversation: Conversation):
    """
    Compile one line of the program. This returns nothing, but will either:
    - append a command to statements
    - append a command to the last map in the stack
    - pop the last map in the stack and append it to statements, calling this function again.
    """
    # Step 1: Classify the line type and get tools in one call

    if map_stack:
        allowed_commands = ["Map", "Command", "EndMap"]
        last_map = map_stack[-1].dimension.prompt
    else:
        allowed_commands = ["Map", "Command"]
        last_map = None
    schema = get_compile_schema(allowed_commands)

    classification_response = conversation.chat(
        classification_prompt(line, last_map), 
        response_schema=schema
    )

    classification_data = json.loads(classification_response)
    line_type = classification_data["type"]
    tools = classification_data["tools"]

    if line_type == "EndMap":
        if map_stack:
            map_stack.pop()
            advance(line, statements, map_stack, conversation)
        else:
            # Try to correct the LLM's classification
            retry_response = conversation.chat(
                retry_classification_prompt(line),
                response_schema=schema,
            )
            retry_data = json.loads(retry_response)
            line_type = retry_data["type"]
            tools = retry_data["tools"]

    # Step 2: Generate AST node based on type and handle nesting
    elif line_type == "Map":
        # Create new map and push to stack
        new_map = _parse_map_line(line, tools)
        if map_stack:
            map_stack[-1].body.statements.append(new_map)
        else:
            statements.append(new_map)
        map_stack.append(new_map)

    elif line_type == "Command":
        command = _parse_command_line(line, tools)

        # If we're inside a map, add to its body, otherwise add to main statements
        if map_stack:
            map_stack[-1].body.statements.append(command)
        else:
            statements.append(command)
    else:
        raise ValueError(f"Unknown line type '{line_type}'")

def compile(lines: list[str]) -> Program:
    """
    Compile a vibe into an program.

    Algorithm:
    1. Read file line by line
    2. For each non-empty line:
       a. Ask LLM: "What should we do at this statement?" (Map/EndMap/Command)
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
        try:
            advance(line, statements, map_stack, conversation)
        except Exception as e:
            raise ValueError(f"Failed to compile line {line_num}: '{line}'") from e

    return Program(statements=statements)


def _parse_map_line(line: str, tools: list[str]) -> Map:
    """Parse a map line into a Map AST node."""
    # Augment the prompt to request JSON list format
    augmented_prompt = require_json_list_prompt(line)
    dimension_command = Command(prompt=augmented_prompt, tools=tools)
    return Map(dimension=dimension_command, body=Program(statements=[]))


def _parse_command_line(line: str, tools: list[str]) -> Command:
    """Parse a command line into a Command AST node."""
    return Command(prompt=line, tools=tools)
