from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, model_validator

from src.schemas import JsonSchema
from src.tools import Tool


class Command(BaseModel):
    node_type: Literal["Command"] = "Command"
    prompt: str
    tools: Sequence[Tool] = []
    files: list[str] = []
    response_schema: JsonSchema | None = None

    def __str__(self) -> str:
        tools_str = (
            ", ".join([t.__class__.__name__ for t in self.tools])
            if self.tools
            else "none"
        )
        files_str = ", ".join(self.files) if self.files else "none"
        return f"Command('{self.prompt}', tools=[{tools_str}], files=[{files_str}])"

    @model_validator(mode="after")
    def tools_or_schema(self):
        assert not (self.tools and self.response_schema), (
            "Gemini doesn't support tools and schema in the same request"
        )
        return self


class Map(BaseModel):
    node_type: Literal["Map"] = "Map"
    dimension: Command
    body: "Program"

    def __str__(self) -> str:
        # Indent the body content properly
        body_str = str(self.body).replace("\n", "\n  ")
        s = f"Map(\n  dimension: {self.dimension}\n  body: {body_str})"
        return s


Statement = Map | Command


class Program(BaseModel):
    statements: list[Statement] = []

    def __str__(self) -> str:
        if not self.statements:
            return "Program([])"

        statements_str = ""
        for i, stmt in enumerate(self.statements):
            # Each statement gets properly indented with all its nested content
            stmt_str = str(stmt).replace("\n", "\n  ")
            statements_str += f"  {i + 1}. {stmt_str}\n"

        return f"Program([\n{statements_str}])"
