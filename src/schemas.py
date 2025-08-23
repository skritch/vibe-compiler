TOOLS_SCHEMA = {
    "type": "array",
    "items": {"type": "string", "enum": ["url_context", "search"]},
    "description": "List of unique tool names needed to execute this command",
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
