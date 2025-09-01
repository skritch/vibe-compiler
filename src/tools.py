from abc import ABC
from typing import Literal, Union, Annotated

from pydantic import BaseModel, Field


class ToolBase(ABC):
    tool_name: str

    def to_dict(self): 
        raise NotImplementedError


class GenericTool(ToolBase, BaseModel):
    tool_type: Literal['Generic'] = 'Generic'
    tool_name: str
    body: dict

    def to_dict(self): 
        return self.body


# GEMINI Built-ins:

UrlContext = GenericTool(tool_name="url_context", body={"url_context": {}})
GoogleSearch = GenericTool(tool_name="search", body={"google_search": {}})


# Local Tools


class ToolParameter(BaseModel):
    type: Literal['object', 'array', 'string', 'float', 'int', 'boolean']
    description: str
    enum: list | None = None

class LocalTool(ToolBase, BaseModel):
    tool_type: Literal['Local'] = 'Local'
    tool_name: str
    name: str
    description: str
    parameters: list[ToolParameter] = []
    required: list[str] = []

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

# Might be nice to autogenerate tools from local python functions?
# Oh that's in the Gemini lib. well shit.
ReadFile = LocalTool(
    tool_name="read_file",
    name="ReadFile",
    description="Read a file on the local filesystem within the current directory. The full contents of the file will be appended as text to the conversation.",
    parameters=[
        ToolParameter(
            type='string', 
            description="The path to the file you want to read",
        )
    ],
    required=['path']
)
# TODO: implement ReadFile

Tool = Annotated[GenericTool | LocalTool, Field(discriminator='tool_type')]

TOOLS_BY_NAME = {
    t.tool_name: t 
    for t in [UrlContext, GoogleSearch, ReadFile]
}
TOOL_NAMES = list(TOOLS_BY_NAME.keys())
