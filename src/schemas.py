TOOLS_SCHEMA = {
    "type": "array",
    "items": {"type": "string", "enum": ["url_context", "search"]},
    "description": "List of unique tool names needed to execute this command",
}

FILES_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "description": "List of filenames which should be uploaded when executing this command.",
}

STRING_LIST_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "description": "List of strings",
}

GENERIC_LIST_SCHEMA = {
    "type": "array",
    "items": {},
    "description": "List of any objects",
}

ALL_COMMANDS = ["Map", "EndMap", "Command"]
def get_compile_schema(allowed_commands: list[str]):
    assert all(c in ALL_COMMANDS for c in allowed_commands)
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": allowed_commands,
                "description": "The type of statement this line represents",
            },
            "tools": TOOLS_SCHEMA,
            "files": FILES_SCHEMA
        },
        "required": ["type", "tools"],
    }
