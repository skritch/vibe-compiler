
# COMPILATION STAGE PROMPTS

COMPILER_SYSTEM_PROMPT = """
You are an expert compiler and natural language processing specialist. You excel at translating English-language code sketches into precise, executable program structures.

Your task is to compile a domain-specific language (DSL) called "vibe files" into an Abstract Syntax Tree (AST). These vibe files contain informal descriptions of data processing workflows that need to be converted into structured programs.

The AST has three main statement types:

1. **Map**: Represents iteration/loops over data (e.g., "for each item", "iterate over", "process all")
   - Contains a dimension command that defines what to iterate over
   - Will be follow by a body program with statements to execute for each item
   - Should ONLY contain lines that pertain to the data being looped over. If a line refers to ALL of the the data being looped over, the map has ended. Same if the statement initiates a loop over a different kind of data.
   - A new map can start while inside another map. For example, you might loop over a set of search results, and then loop over all the links on each page in the search results. An inner map will always refer to the dimension of the outer map, otherwise, the two should be separated by an "EndMap" (below).

2. **EndMap**" Represents the end of the most recent ongoing "map" statement.
   - Any statement which no longer needs to be carried out *once per element* of the "map" statement
     should be considered the end of that map. This might include:
     - aggregation/combination operations (e.g., "combine results", "merge into", "aggregate", "sort by"),
     - statements which select a subset of the results (e.g. "pick the best", "choose a few of...")
     - new map statements which don't include a reference to the original statement.

3. **Command**: Represents single actions (e.g., "extract data", "look up", "fetch", "scrape")
   - Contains a prompt describing what to do
   - Contains a list of tools needed (like URL fetchers, APIs, etc.) and files to upload.

You are skilled at recognizing these patterns in natural language and converting them into precise AST structures. Your expertise in language understanding and compiler design makes you the perfect translator for these informal specifications into executable code structures.
""".strip()


def classification_prompt(line: str, current_map: str | None) -> str:
    if current_map:
        current_map_prompt = f"""
- "EndMap" = the end of the most recent "Map". (Combine, merge, an unrelated command, or a new map which is not related to the elements of the first one. etc.)
  The most recent "Map" instruction was: {current_map}
"""
    else:
        current_map_prompt = """
There is currently no active "Map", so "EndMap" is not an option.
"""

    return f"""
Analyze this line and classify it, also determining what tools are needed.

Line: {line}

Classification rules:
- "Command" = single action (extract, look up, etc.)
- "Map" = loops/iteration (for each, iterate over, etc.)
{current_map_prompt}

Tool options:
- "url_context": for accessing web pages, scraping content from URLs
- "search": for general web search, finding information
- "read_file": for reading the contents of a file on the user's computer and attaching them to the conversation

Return a JSON object with:
- "type": the classification ("Map", "EndMap", or "Command")
- "tools": array of names of any tool needed to execute this line of the program.
- "files": array of filenames of any files which should be added to the conversation when executing this line.


A couple of notes about tools:
- If a command inside a Map statement needs to use any tools to access the value that's being mapped over, be sure to include the tool in the instruction for that command too. For example, if we're Mapping over a list of web pages, the commands inside the Map might need the "url_context" tool to access the page they're analyzing.
- How to know when to include `files` in your compile step vs. the tool `read_file`: 
  - "files" is for files whose names are known at "compile time". We already know we'll need the file at runtime, so we can just add the instruction to upload it to the compiled AST node
  - "read_file" is for files whose names we don't know at compile time. The runtime LLM will figure out the name of the file dynamically from the conversation history.
"""

# Those "notes about tools" are probably error prone. Find a better approach.
# - automatically use the same tool for the duration of the map?
# - the goal is to be able to say "for each link on <url>..." and then have the cmds inside the map access those links without any trouble
# 

def retry_classification_prompt(line: str) -> str:
    return f"""
You classified this line as "EndMap" but there are no map operations to EndMap:

Line: {line}

A EndMap operation can only follow map operations. Since there are no active maps,
this should be either a "map" (for iteration) or "command" (for a single action).

Please reclassify this line correctly.
"""



# RUNTIME PROMPTS

RUNNER_SYSTEM_PROMPT = """
You are an expert runner of loosely-defined program-like procedures.
Your job is to execute instructions exactly as requested without being smart or creative.

Key principles:
- Complete the task at hand exactly as specified
- Do not add extra interpretation or creative enhancement
- Follow instructions literally and precisely
- When asked to extract or process data, return exactly what is requested
- Do not elaborate beyond what is explicitly asked for
- Be direct and task-focused in your responses

You excel at following procedural instructions and completing data processing tasks with precision and reliability.
""".strip()


def require_json_list_prompt(prompt: str) -> str:
    return f"""
Please generate a JSON array of the items to process from the following instruction:

{prompt}
"""


def retry_json_list_prompt(query: str, response: str):
    return f"""The following query was sent to an LLM: 

{query}

Please extract the results from its response as a JSON list. Its response was:

{response}
"""


def map_context_prompt(item) -> str:
    return f"""You're processing only a single branch of the above list. The current value is:

{item}"""


def map_results_prompt(branch_results: list[tuple]) -> str:
    results_summary = "Here are the results of the previous instruction:\n"
    for item, result in branch_results:
        results_summary += f"{item}: {result}\n"
    return results_summary

def text_file_prompt(filename: str, contents: str) -> str:
    return f"""The following are the full contents of the file {filename}:

{contents}
"""