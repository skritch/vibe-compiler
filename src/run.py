import json
from copy import deepcopy

from tqdm import tqdm

from src.prompts import map_context_prompt, map_results_prompt

from .compile import compile
from .llm import LLM, Conversation
from .program import Command, Map, Program
from .tools import URL, Search

RUNNER_SYSTEM_PROMPT = """
You are an expert runner of loosely-defined program-like procedures.
Your job is to execute instructions exactly as requested without being smart or creative.

Key principles:
- Complete the task at hand exactly as specified
- Do not add extra interpretation or creative enhancement
- Follow instructions literally and precisely
- When asked to extract or process data, return exactly what is requested
- Do not elaborate beyond what is explicitly asked for
- Be direct and task-focused in your responses

You excel at following procedural instructions and completing data processing tasks with precision and reliability.
""".strip()


def run_program(program: Program, llm: LLM | None = None) -> str:
    """
    Execute a compiled vibe program.

    Args:
        program: The compiled Program to execute
        llm: Optional LLM instance (defaults to LLM.from_env())

    Returns:
        Final execution result as a string
    """
    if llm is None:
        llm = LLM.from_env()

    # Start with a fresh conversation using the runner system prompt
    conversation = llm.converse(RUNNER_SYSTEM_PROMPT)

    return _execute_program(program, conversation)


def _copy_conversation(conv: Conversation) -> Conversation:
    """Create a deep copy of a conversation with its history."""
    new_conv = Conversation(conv.llm, conv.model, conv.system_prompt)
    new_conv.contents = deepcopy(conv.contents)
    return new_conv


def _execute_program(program: Program, conversation: Conversation) -> str:
    """Execute a program with the given conversation stack."""
    last_result = ""

    for statement in program.statements:
        if isinstance(statement, Command):
            last_result = _execute_command(statement, conversation)

        elif isinstance(statement, Map):
            last_result = _execute_map(statement, conversation)

        else:
            raise ValueError(f"Unknown statement type: {type(statement)}")

    return last_result


def _execute_command(command: Command, conversation: Conversation) -> str:
    """Execute a command statement.

    Adds one chat/response to the conversation."""
    # Convert tool names to Tool objects
    tools = []
    for tool_name in command.tools:
        if tool_name == "url_context":
            tools.append(URL)
        elif tool_name == "search":
            tools.append(Search)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    # Execute the command
    result = conversation.chat(command.prompt, tools=tools)
    return result


def _execute_map(map_stmt: Map, conversation: Conversation) -> str:
    """
    Execute a map statement with iteration over a list.

    Adds a chat/response for the map statement, a summary of results,
    and a chat/response for the reduce statement if one is given.
    """

    # Note: Gemini doesn't support a function + json list in the same command,
    # Gemini Pro might actually? TODO.
    # so we don't bother and delegate to `_execute_command`. Other providers might.
    list_response = _execute_command(map_stmt.dimension, conversation)

    # Parse the JSON response
    first_bracket, last_bracket = list_response.index("["), list_response.rindex("]")

    if (first_bracket is None) or (last_bracket is None):
        raise ValueError("Response was not a list")

    bracketed_part = list_response[first_bracket : last_bracket + 1]
    try:
        items_list = json.loads(bracketed_part)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse list response: {e}")

    # Process each item in the list
    branch_results = []
    for item in tqdm(items_list, desc="Processing map items", unit="item", ncols=0):
        # Fork the conversation for this branch
        branch_conversation = _copy_conversation(conversation)

        map_prompt = map_context_prompt(item)

        # Add the context message for this specific item
        branch_conversation.contents.append(
            {"role": "user", "parts": [{"text": map_prompt}]}
        )

        # Execute the map's body program with the forked conversation
        branch_result = _execute_program(map_stmt.body, branch_conversation)

        branch_results.append((item, branch_result))

    results_summary = map_results_prompt(branch_results)

    # Add the combined results to the original conversation
    conversation.contents.append({"role": "user", "parts": [{"text": results_summary}]})
    # Execute the reduce operation if present
    if map_stmt.reduce:
        reduce_result = conversation.chat(map_stmt.reduce.prompt)
        return reduce_result
    else:
        # If no reduce, return the summary
        return results_summary


def run_vibe(vibe_file: str, llm: LLM | None = None) -> str:
    """
    Compile and run a vibe file in one step.

    Args:
        vibe_file: Path to the .vibe file
        llm: Optional LLM instance (defaults to LLM.from_env())

    Returns:
        Final execution result as a string
    """

    program = compile(vibe_file)
    return run_program(program, llm)
