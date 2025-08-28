


cost
- use a cheaper LLM for compilation. maybe use heuristics first ("for..in")

speed
- batch big loops smartly
- parallelize a little bit


correctness
- test a nested map
- add a unit test? lol


compatibility
- factor Gemini out into `providers`
- add an openai provider. probably just use REST. test it somehow.
- figure out if Gemini pro can handle json + functions, or w/e
https://github.com/google-gemini/deprecated-generative-ai-python/issues/515#issuecomment-2304249426 is talking about


features
- support comments in JS or python format 

- add some "error handling" (i.e. pester the AI to retry once. Possibly allow failures inside maps and just return the failed result.)
- parallelize a little bit
- delimit "results" better.
- use a different/simpler model for compiling
- Log between "running" and "compiling"
- maybe remove "reduce" as a separate line you actually run. can just be "end map"
- wrap the "for loop" prompt in a better prompt or something
