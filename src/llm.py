import os
from urllib.parse import urljoin

import requests

from .tools import Tool


class LLM:
    def __init__(self, api_key, base_url: str, model: str | None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model

    @classmethod
    def from_env(cls):
        provider = os.environ["LLM_PROVIDER"]

        api_key = os.environ[f"{provider.upper()}_API_KEY"]
        url = os.environ[f"{provider.upper()}_URL"]
        model = os.environ.get(f"{provider.upper()}_MODEL")
        return cls(api_key, url, model)

    def chat(
        self,
        message: str | list[dict],
        system_instruction: str | None = None,
        tools: list[Tool] | None = None,
        model: str | None = None,
        response_schema: dict | None = None,
    ):
        """
        Chat request with Gemini's native format.

        TODO: use OpenAI model and do our own tool-calling.
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
        response = requests.post(
            f"{self.base_url}/{model}:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            json=payload,
        )
        if not response.ok:
            print(response.text)
            response.raise_for_status()

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

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

    def chat(self, message: str, **kwargs):
        # Add user message to contents
        self.contents.append({"role": "user", "parts": [{"text": message}]})

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
