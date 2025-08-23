


- factor Gemini out into `providers`
- add an openai provider. probably just use REST. test it somehow.
- add a cli that takes a `;`-delimited script
- support comments in JS or python format
- test a nested map
- add a unit test? lol
- figure out if Gemini pro can handle json + functions, or w/e
https://github.com/google-gemini/deprecated-generative-ai-python/issues/515#issuecomment-2304249426 is talking about

- add some "error handling" (i.e. pester the AI to retry once. Possibly allow failures inside maps and just return the failed result.)
- parallelize a little bit
- debug log everything to a file
- delimit "results" better.
- run a compiled 