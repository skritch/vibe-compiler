COMPILER_SYSTEM_PROMPT = """
You are an expert compiler and natural language processing specialist. You excel at translating English-language code sketches into precise, executable program structures.

Your task is to compile a domain-specific language (DSL) called "vibe files" into an Abstract Syntax Tree (AST). These vibe files contain informal descriptions of data processing workflows that need to be converted into structured programs.

The AST has three main statement types:

1. **Map** - Represents iteration/loops over data (e.g., "for each item", "iterate over", "process all")
   - Contains a dimension command that defines what to iterate over
   - Contains a body program with statements to execute for each item

2. **Reduce** - Represents aggregation/combination operations (e.g., "combine results", "merge into", "aggregate")
   - Contains a body program that defines how to combine the data

3. **Command** - Represents single actions (e.g., "extract data", "look up", "fetch", "scrape")
   - Contains a prompt describing what to do
   - Contains a list of tools needed (like URL fetchers, APIs, etc.)

You are incredibly skilled at recognizing these patterns in natural language and converting them into precise AST structures. Your expertise in language understanding and compiler design makes you the perfect translator for these informal specifications into executable code structures.
""".strip()


def classification_prompt(line: str) -> str:
    return f"""
Analyze this line and classify it, also determining what tools are needed.

Line: {line}

Classification rules:
- "map" = loops/iteration (for each, iterate over, etc.)
- "reduce" = combining/aggregating results (combine, merge, etc.)  
- "command" = single action (extract, look up, etc.)

Tool options:
- "url_context": for accessing web pages, scraping content from URLs
- "search": for general web search, finding information

Return a JSON object with:
- "type": the classification ("map", "reduce", or "command")  
- "tools": array of tool names needed (can be empty for reduce statements)

For map statements, the tools should be for the dimension command (what to iterate over).
"""


def tools_selection_prompt(line: str, available_tools: list[str]) -> str:
    return f"""
For this command line: "{line}"

Which tools are needed? Choose from: {available_tools}

- url_context: for accessing web pages, scraping content from URLs
- search: for general web search, finding information

Return only a JSON array of tool names.

Example: ["url_context"]
"""


def retry_classification_prompt(line: str) -> str:
    return f"""
You classified this line as "reduce" but there are no map operations to reduce:

Line: {line}

A reduce operation can only follow map operations. Since there are no active maps, 
this should be either a "map" (for iteration) or "command" (for a single action).

Please reclassify this line correctly.
"""
