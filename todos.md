


cost
- use a cheaper LLM for compilation. maybe use heuristics first ("for..in")

speed
- batch big loops smartly
- parallelize a little bit


correctness
- test a nested map
- add a unit test? lol
- add test examples and expected compiled outputs


compatibility
- factor Gemini out into `providers`
- add an openai provider. probably just use REST. test it somehow.
- figure out if Gemini pro can handle json + functions, or w/e
https://github.com/google-gemini/deprecated-generative-ai-python/issues/515#issuecomment-2304249426 is talking about
- okay, we can get a json list by running a second query. I don't seem to have free Gemini access.


features
- support comments in JS or python format 
- wrap the "for loop" prompt in a better prompt or something
- A separate "fold" or "for" with ongoing state.
  - Then we need to the compiler to be able to distinguish a Map (parallel, no state) from a For (state)
  - This might require looking ahead at the whole program inside the map?
- delimit "results" better.
- possibility resume execution from a written-out conversation
- support uploading a file
- support writing results to a file (instead of merely viewing in the conversation)

Overall next step is: get organized about input/output files.
- default output should be named like the input (vibe -> vibec, vibec -> txt)
- should always write the whole conversation to .data/ or a log dir
- print various retrying progress as we go


robustness
- add some "error handling" (i.e. pester the AI to retry once. Possibly allow failures inside maps and just return the failed result.)
- parallelize a little bit
- I probably need to log retries and the like somewhere too
- when running from .vibe, write the .vibec out as a checkpoint
- Log between "running" and "compiling"

  