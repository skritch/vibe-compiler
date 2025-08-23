

from src.llm import LLM
from src.tools import *

prompt = 'list all the neighborhoods on this page: https://www.forsythrealty.com/neighborhoods'


print(LLM.from_env().chat(prompt, tools=[URL]))