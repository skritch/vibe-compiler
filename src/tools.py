from pydantic import BaseModel


class Tool(BaseModel):
    tool_name: str

    def to_dict(self):
        raise NotImplementedError

class GenericTool(Tool):
    body: dict

    def to_dict(self): return self.body

# GEMINI Built-ins:

UrlContext = GenericTool(tool_name="url_context", body={"url_context": {}})
GoogleSearch = GenericTool(tool_name="google_search", body={"google_search": {}})


TOOLS_BY_NAME = {t.tool_name: t for t in [UrlContext, GoogleSearch]}
