from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class Command:
    prompt: str
    tools: list[str]

    def __str__(self) -> str:
        tools_str = ", ".join(self.tools) if self.tools else "none"
        return f"Command('{self.prompt}', tools=[{tools_str}])"


@dataclass
class Map:
    dimension: Command
    body: "Program"

    def __str__(self) -> str:
        # Indent the body content properly
        body_str = str(self.body).replace("\n", "\n  ")
        return f"Map(\n  dimension: {self.dimension}\n  body: {body_str}\n)"


@dataclass
class Reduce:
    prompt: str

    def __str__(self) -> str:
        return f"Reduce('{self.prompt}')"


Statement = Map | Reduce | Command


@dataclass
class Program:
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
