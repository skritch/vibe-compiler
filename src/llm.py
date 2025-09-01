import os
import time
from typing import Literal

import requests

from src.providers.gemini import parse_retry_delay

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
        _log_file.write(f"{role}: {payload}\n")
        _log_file.flush()


class LLM:
    def __init__(self, api_key, base_url: str, model: str | None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @classmethod
    def from_env(cls):
        provider = os.environ["LLM_PROVIDER"]

        # TODO: with multiple providers, just instantiate the
        # one we want here.

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

        _log("USER", payload)

        # Retry logic with exponential backoff
        # TODO: set these parameters somewhere.
        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
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
                    result = response.json()["candidates"][0]["content"]["parts"][0][
                        "text"
                    ]
                    _log("ASSISTANT", result)
                    return result
                except:
                    print(response.json()["candidates"][0])
                    raise

            # Handle rate limiting (429 errors)
            if response.status_code == 429:
                if attempt < max_retries:
                    # Try to get retry delay from response
                    retry_delay = parse_retry_delay(response) or base_delay * (
                        2**attempt
                    )

                    print(
                        f"Rate limited. Retrying in {retry_delay:.1f}s... (attempt {attempt + 1}/{max_retries})"
                    )
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
        self.conversation: list[dict] = []

    def chat(
        self,
        message: str,
        tools: list[Tool] | None = None,
        response_schema: dict | None = None,
    ) -> str:
        # I suppose we could accept a different model or system instruction here, but.

        self.append_text(message, "user")

        # Send full conversation history
        response = self.llm.chat(
            self.conversation,
            system_instruction=self.system_prompt,
            tools=tools,
            response_schema=response_schema,
        )

        # Add assistant response to contents
        self.append_text(response, "model")

        return response

    def append_text(self, text: str, role: Literal["user"] | Literal["model"]):
        """
        Append some text to the conversation without calling the LLM.
        """
        self.conversation.append({"role": role, "parts": [{"text": text}]})

    def append_pdf(self, filename):
        """
        Errors if the file is greater than 20MB (Gemini max size for base64 uploads.)

        Note: Gemini intends for this to be used for PDFs, but we won't enforce that.
        """
        import base64

        # Check if file exists
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        # Check file size (20MB limit)
        file_size = os.path.getsize(filename)
        max_size = 20 * 1024 * 1024  # 20MB in bytes
        if file_size > max_size:
            raise ValueError(
                f"File size {file_size} bytes exceeds 20MB limit ({max_size} bytes)"
            )

        # Read and encode the file
        with open(filename, "rb") as file:
            file_content = file.read()
            base64_content = base64.b64encode(file_content).decode("utf-8")

        self.conversation.append(
            {"inline_data": {"mime_type": "application/pdf", "data": base64_content}}
        )
