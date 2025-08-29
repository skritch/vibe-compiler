from typing import Literal, Union
from pydantic import BaseModel, model_serializer


class Command(BaseModel):
    node_type: Literal["Command"] = "Command"
    prompt: str
    tools: list[str]
    files: list[str] = []

    def __str__(self) -> str:
        tools_str = ", ".join(self.tools) if self.tools else "none"
        files_str = ", ".join(self.files) if self.files else "none"
        return f"Command('{self.prompt}', tools=[{tools_str}], files=[{files_str}])"


class Map(BaseModel):
    node_type: Literal["Map"] = "Map"
    dimension: Command
    body: "Program"

    def __str__(self) -> str:
        # Indent the body content properly
        body_str = str(self.body).replace("\n", "\n  ")
        s = f"Map(\n  dimension: {self.dimension}\n  body: {body_str})"
        return s


Statement = Union[Map, Command]


class Program(BaseModel):
    statements: list[Statement]

    def __str__(self) -> str:
        if not self.statements:
            return "Program([])"

        statements_str = ""
        for i, stmt in enumerate(self.statements):
            # Each statement gets properly indented with all its nested content
            stmt_str = str(stmt).replace("\n", "\n  ")
            statements_str += f"  {i + 1}. {stmt_str}\n"

        return f"Program([\n{statements_str}])"
