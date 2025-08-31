import json
from copy import deepcopy

from tqdm import tqdm

from src.prompts import RUNNER_SYSTEM_PROMPT, map_context_prompt, map_results_prompt, retry_json_list_prompt
from src.schemas import GENERIC_LIST_SCHEMA

from .compile import compile
from .files import serialize_to_base64
from .llm import LLM, Conversation
from .program import Command, Map, Program
from .tools import URL, Search



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
        else:
            last_result = _execute_map(statement, conversation)
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
    
    # Build message parts - start with text
    parts: list[dict] = [{"text": command.prompt}]
    
    # Add file uploads if any
    for filename in command.files:
        try:
            base64_data = serialize_to_base64(filename)
            parts.append({
                "inline_data": {
                    "mime_type": "application/pdf", 
                    "data": base64_data
                }
            })
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: Could not upload file {filename}: {e}")
            continue
    
    # Create message in the format expected by conversation.chat
    message = [{"parts": parts}]
    
    # Execute the command
    result = conversation.chat(message, tools=tools, )
    return result


def _parse_maybe_list(response: str) -> list | None:
    # Parse the JSON response
    first_bracket, last_bracket = response.index("["), response.rindex("]")

    # TODO: if we can't just parse a list, call the LLM again with the list schema and the previous response, 
    # but not the tool.
    if (first_bracket is None) or (last_bracket is None):
        return None

    bracketed_part = response[first_bracket : last_bracket + 1]
    try:
        items = json.loads(bracketed_part)
    except (json.JSONDecodeError, ValueError) as e:
        return None
    if isinstance(items, list):
        return items
    else:
        return None
    
def retry_list(command: Command, response: str, conversation: Conversation):
    # Or use the LLM directly without the conversation?
    return conversation.chat(
        retry_json_list_prompt(command.prompt, response),
        response_schema=GENERIC_LIST_SCHEMA
    )

def _execute_map(map_stmt: Map, conversation: Conversation) -> str:
    """
    Execute a map statement with iteration over a list.

    Adds a chat/response for the map statement and a summary of results.
    """

    # Note: Gemini doesn't support function calls + json response format in the chat.
    # so we don't bother and delegate to `_execute_command`. Other providers might.
    # Gemini Pro might actually? TODO.

    list_response = _execute_command(map_stmt.dimension, conversation)

    # TODO: if we can't just parse a list, call the LLM again with the list schema and the previous response, 
    # but not the tool.
    items_list = _parse_maybe_list(list_response)
    if items_list is None:
        items_list = retry_list(map_stmt.dimension, list_response, conversation)
        if not isinstance(items_list, list):
            raise RuntimeError(f"Didn't receive a list for {map_stmt}")

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
    return results_summary

