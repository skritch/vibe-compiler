TOOLS_SCHEMA = {
    "type": "array",
    "items": {"type": "string", "enum": ["url_context", "search"]},
    "description": "List of unique tool names needed to execute this command",
}

# TODO: gemini uses a stripped down jsonschema it looks like, this won't work.
COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "The natural language description of what this command should do",
        },
        "tools": TOOLS_SCHEMA,
    },
    "required": ["prompt", "tools"],
}

MAP_SCHEMA = {
    "type": "object",
    "properties": {
        "dimension": {
            "$ref": "#/definitions/command",
            "description": "The command that defines what to iterate over",
        },
        "body": {
            "type": "array",
            "items": {"$ref": "#/definitions/statement"},
            "description": "List of statements to execute for each iteration",
        },
    },
    "required": ["dimension", "body"],
    "definitions": {"command": COMMAND_SCHEMA},
}

REDUCE_SCHEMA = {
    "type": "object",
    "properties": {
        "body": {
            "type": "array",
            "items": {"$ref": "#/definitions/statement"},
            "description": "List of statements that define how to combine/reduce the data",
        }
    },
    "required": ["body"],
}

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ["map", "reduce", "command"],
            "description": "The type of statement this line represents",
        },
        "tools": TOOLS_SCHEMA,
    },
    "required": ["type", "tools"],
}
