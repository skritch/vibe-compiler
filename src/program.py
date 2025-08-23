from dataclasses import dataclass
from typing import Sequence

from tools import Tool


@dataclass
class Command:
    prompt: str
    tools: list[Tool]


@dataclass
class Map:
    dimension: Command
    body: "Program"


@dataclass
class Reduce:
    body: "Program"


Statement = Map | Reduce | Command


@dataclass
class Program:
    statements: Sequence[Statement]