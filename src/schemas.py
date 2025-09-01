import json
from jsonschema import Draft7Validator
from pydantic import BaseModel, field_validator


class JsonSchema(BaseModel):
    jsonschema: dict

    @field_validator('jsonschema')
    @classmethod
    def validate_schema(cls, v):
        Draft7Validator.check_schema(v)
        return v

    def __str__(self):
        return json.dumps(self.jsonschema)


TOOLS_SCHEMA = JsonSchema(
    jsonschema={
        "type": "array",
        "items": {"type": "string", "enum": ["url_context", "search"]},
        "description": "List of unique tool names needed to execute this command",
    }
)

FILES_SCHEMA = JsonSchema(
    jsonschema={
        "type": "array",
        "items": {"type": "string"},
        "description": "List of filenames which should be uploaded when executing this command.",
    }
)

STRING_LIST_SCHEMA = JsonSchema(
    jsonschema={
        "type": "array",
        "items": {"type": "string"},
        "description": "List of strings",
    }
)

GENERIC_LIST_SCHEMA = JsonSchema(
    jsonschema={
        "type": "array",
        "items": {},
        "description": "List of any objects",
    }
)

ALL_COMMANDS = ["Map", "EndMap", "Command"]


def get_compile_schema(allowed_commands: list[str]) -> JsonSchema:
    assert all(c in ALL_COMMANDS for c in allowed_commands)
    return JsonSchema(
        jsonschema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": allowed_commands,
                    "description": "The type of statement this line represents",
                },
                "tools": TOOLS_SCHEMA.jsonschema,
                "files": FILES_SCHEMA.jsonschema,
            },
            "required": ["type", "tools"],
        }
    )
