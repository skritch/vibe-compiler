from collections.abc import Iterable
from typing import Annotated

from pydantic import AfterValidator, BaseModel
from tqdm import tqdm

from src.llm import LLM, Conversation
from src.program import Command, Map, Program, Statement
from src.prompts import (
    COMPILER_SYSTEM_PROMPT,
    classification_prompt,
    require_json_list_prompt,
    retry_classification_prompt,
)
from src.schemas import GENERIC_LIST_SCHEMA, get_compile_schema
from src.tools import TOOLS_BY_NAME


def assert_in(x, allowed: Iterable):
    assert x in allowed, f"{x} not in {allowed}"
    return x

class CompileResponse(BaseModel):
    type: Annotated[str, AfterValidator(lambda t:  assert_in(t, ["Map", "EndMap", "Command"]))]
    tools: Annotated[list[str], AfterValidator(lambda ts: [assert_in(t, TOOLS_BY_NAME) for t in ts])]
    files: list[str] = []


def parse_tools(tools: list[str]):
    # TODO: parse tool calls
    return [TOOLS_BY_NAME[t] for t in tools]


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
    non_empty_lines = [line.strip() for line in lines if line.strip()]

    for line_num, line in enumerate(
        tqdm(non_empty_lines, desc="Compiling lines", unit="line", ncols=0)
    ):
        try:
            advance(line, statements, map_stack, conversation)
        except Exception as e:
            raise ValueError(f"Failed to compile line {line_num}: '{line}'") from e

    return Program(statements=statements)


def advance(
    line: str,
    statements: list[Statement],
    map_stack: list[Map],
    conversation: Conversation,
):
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
        classification_prompt(line, last_map), response_schema=schema.schema_
    )

    compiled = CompileResponse.model_validate_json(classification_response)

    if compiled.type == "EndMap":
        if map_stack:
            map_stack.pop()
            advance(line, statements, map_stack, conversation)
        else:
            # Try to correct the LLM's classification
            retry_response = conversation.chat(
                retry_classification_prompt(line),
                response_schema=schema.schema_,
            )
            compiled = CompileResponse.model_validate_json(retry_response)

    # Step 2: Generate AST node based on type and handle nesting
    elif compiled.type == "Map":
        # Create new map and push to stack

        dim_cmd = Command(
            prompt=require_json_list_prompt(line),
            tools=parse_tools(compiled.tools),
            files=compiled.files,
            # Hack: Gemini doesn't support tools + jsonschema in the same request
            response_schema = GENERIC_LIST_SCHEMA if not compiled.tools else None
        )

        new_map = Map(dimension=dim_cmd, body=Program(statements=[]))

        if map_stack:
            map_stack[-1].body.statements.append(new_map)
        else:
            statements.append(new_map)
        map_stack.append(new_map)

    elif compiled.type == "Command":
        command = Command(
            prompt=line, tools=parse_tools(compiled.tools), files=compiled.files
        )

        # If we're inside a map, add to its body, otherwise add to main statements
        if map_stack:
            map_stack[-1].body.statements.append(command)
        else:
            statements.append(command)

