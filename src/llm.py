import os
import time

import requests

from .tools import Tool

# Global debug file handle
_log_file = None


def set_log_file(filename: str):
    """Enable debug logging to a file."""
    global _log_file
    _log_file = open(filename, "w")


def _log(role: str, payload: dict):
    """Log a message to the debug file if enabled."""
    if _log_file:
        _log_file.write(f'{role}: {payload}\n')
        _log_file.flush()


class LLM:
    def __init__(self, api_key, base_url: str, model: str | None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @classmethod
    def from_env(cls):
        provider = os.environ["LLM_PROVIDER"]

        api_key = os.environ[f"{provider.upper()}_API_KEY"]
        url = os.environ[f"{provider.upper()}_URL"]
        model = os.environ[f"{provider.upper()}_MODEL"]
        print(f"Using model {model} from provider {provider}")
        return cls(api_key, url, model)

    def chat(
        self,
        message: str | list[dict],
        system_instruction: str | None = None,
        tools: list[Tool] | None = None,
        model: str | None = None,
        response_schema: dict | None = None,
    ) -> str:
        """
        Chat request with Gemini's native format.

        TODO: use OpenAI model and do our own tool-calling.
        TODO: log the tools in our requests somewhere.
        """
        model = model or self.model
        assert model

        if isinstance(message, str):
            contents = [{"parts": [{"text": message}]}]
        else:
            contents = message

        payload: dict = {"contents": contents}

        if system_instruction:
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
        
        if tools:
            payload["tools"] = [t.body for t in tools]

        if response_schema:
            payload["generationConfig"] = {
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
            }
        

        _log('USER', payload)

        # Retry logic with exponential backoff
        # TODO: set these parameters somewhere.
        max_retries = 5
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            response = requests.post(
                f"{self.base_url}/{model}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=payload,
            )
            
            if response.ok:
                try:
                    result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    _log('ASSISTANT', result)
                    return result
                except:
                    print(response.json()["candidates"][0])
                    raise
            
            # Handle rate limiting (429 errors)
            if response.status_code == 429:
                if attempt < max_retries:
                    # Try to get retry delay from response
                    retry_delay = base_delay
                    try:
                        error_data = response.json()
                        # Look for RetryInfo in error details
                        for detail in error_data.get("error", {}).get("details", []):
                            if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                                retry_delay_str = detail.get("retryDelay", "1s")
                                # Parse delay like "7s"
                                if retry_delay_str.endswith("s"):
                                    retry_delay = float(retry_delay_str[:-1]) + 0.5
                                break
                    except:
                        # Fall back to exponential backoff
                        retry_delay = base_delay * (2 ** attempt)
                    
                    print(f"Rate limited. Retrying in {retry_delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            
        # For other errors or final attempt, raise the error
        raise RuntimeError(response.json())

    def converse(self, system_prompt: str, model: str | None = None):
        model = model or self.model
        assert model
        return Conversation(self, model, system_prompt)


class Conversation:
    def __init__(self, llm: "LLM", model: str, system_prompt: str | None = None):
        self.llm = llm
        self.model = model
        self.system_prompt = system_prompt
        self.contents: list[dict] = []

    def chat(self, message: str | list[dict], **kwargs) -> str:
        # Add user message to contents
        if isinstance(message, str):
            self.contents.append({"role": "user", "parts": [{"text": message}]})
        else:
            # message is already in the expected format (list of dicts with parts)
            for msg_part in message:
                self.contents.append({"role": "user", **msg_part})

        # Send full conversation history
        response = self.llm.chat(
            self.contents,
            system_instruction=self.system_prompt,
            model=self.model,
            **kwargs,
        )

        # Add assistant response to contents
        self.contents.append({"role": "model", "parts": [{"text": response}]})

        return response
