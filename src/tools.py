

class Tool:
  def __init__(self, body):
    self.body = body

# GEMINI TOOLS:
URL = Tool({"url_context": {}})
Search = Tool({"google_search": {}})

