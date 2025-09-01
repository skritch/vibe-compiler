from src.program import Command, Map, Program
from src.prompts import require_json_list_prompt
from src.schemas import GENERIC_LIST_SCHEMA, JsonSchema
from tools import Tool


class Vibe:
    """
    Python API to instantiate a Vibe program.

    Once instantiated, the `program` instance variable can be
    run, serialized, etc.
    """

    def __init__(self, program: Program | None):
        self.program: Program = program or Program()

    def append(self, node: Command | Map):
        if self.program.statements[-1].node_type == "Map":
            self.program.statements[-1].body.statements.append(node)
        else:
            self.program.statements.append(node)

    def cmd(self, prompt: str, tools: list[Tool] | None, files: list[str] | None, schema: JsonSchema | dict | None = None):
        if isinstance(schema, dict):
            schema = JsonSchema(schema=schema)
        cmd = Command(prompt=prompt, tools=tools or [], files=files or [], response_schema=schema)
        self.append(cmd)
        return self

    def map(self, prompt: str, tools: list[Tool] | None, files: list[str] | None):
        """
        Add a Map statement to the program, returning a new instance of this
        class to construct the body.

        Usage:

        v = Vibe()
        v.cmd(...)
        m1 = v.map(...)
        m1.cmd(...)
        m2 = m1.map(...)
        m2.cmd()
        m1.cmd()
        v.cmd(...)

        This is equivalent to:

        cmd 1
        for value in m1:
            cmd 2
            for value in m2:
                cmd 3
            cmd 4
        cmd 5
        """

        # TODO: require a list
        dim = Command(
            prompt=require_json_list_prompt(prompt),
            tools=tools or [],
            files=files or [],
            response_schema=GENERIC_LIST_SCHEMA if not tools else None  # Hack for Gemini
        )
        m = Map(dimension=dim, body=Program())
        self.append(m)
        return Vibe(m.body)

