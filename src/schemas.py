import json


class JsonSchema(dict):
    schema_: dict

    def __str__(self):
        return json.dumps(self.schema_)

    # TODO: validate


TOOLS_SCHEMA = JsonSchema(
    schema={
        "type": "array",
        "items": {"type": "string", "enum": ["url_context", "search"]},
        "description": "List of unique tool names needed to execute this command",
    }
)

FILES_SCHEMA = JsonSchema(
    schema={
        "type": "array",
        "items": {"type": "string"},
        "description": "List of filenames which should be uploaded when executing this command.",
    }
)

STRING_LIST_SCHEMA = JsonSchema(
    schema={
        "type": "array",
        "items": {"type": "string"},
        "description": "List of strings",
    }
)

GENERIC_LIST_SCHEMA = JsonSchema(
    schema={
        "type": "array",
        "items": {},
        "description": "List of any objects",
    }
)

ALL_COMMANDS = ["Map", "EndMap", "Command"]


def get_compile_schema(allowed_commands: list[str]):
    assert all(c in ALL_COMMANDS for c in allowed_commands)
    return JsonSchema(
        schema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": allowed_commands,
                    "description": "The type of statement this line represents",
                },
                "tools": TOOLS_SCHEMA.schema_,
                "files": FILES_SCHEMA.schema_,
            },
            "required": ["type", "tools"],
        }
    )
