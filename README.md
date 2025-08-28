# Vibe-Compiler


Vibe-compile a plaintext sequence of instructions into a vibe-program. Then vibe-run it.

For when an open-ended LLM chat is a little too free-form.

This is obviously a terrible idea........ or is it?

Currently only Gemini is supported, and only the single example in `./vibes/` has been tested, which is par for this course.

#### Usage

Here's a program:
```
look up today's date
look up the current phase of the moon
for each sign of the zodiac:
  generate a horoscope for today
select the single most and single least auspicious of all the horoscopes
find the prime factors of today's date in DDMMYY format
then, use all this to divine a portent as to what major event will come to pass today
```


Compiling:
```
uv run python cli.py compile vibes/portent.vibe

Compiling lines: 100% 6/6 [00:11<00:00,  1.85s/line]
Compiled 'vibes/portent.vibe':
Program([
  1. Command('look up today's date', tools=[search])
  2. Command('look up the current phase of the moon', tools=[search])
  3. Map(
    dimension: Command('for each sign of the zodiac:
  
  Please respond with a JSON array of items to process.', tools=[search])
    body: Program([
      1. Command('generate a horoscope for today', tools=[search])
    ]) 
    reduce: Reduce('select the single most and single least auspicious of all the horoscopes') 
  )
  4. Command('find the prime factors of today's date in DDMMYY format', tools=[search])
  5. Command('then, use all this to divine a portent as to what major event will come to pass today', tools=[none])
])
```

Or run:
```
uv run python cli.py run vibes/portent.vibe
```

