import os, time
from typing import Dict, Any, List
from .provider import Provider, ModelOutput

# OpenAI official SDK (Responses API)
from openai import OpenAI

class OpenAIProvider(Provider):
    def __init__(self, model_id: str, temperature: float = 0.2, max_output_tokens: int = 256, request_timeout: int = 60):
        self.client = OpenAI()
        self.model_id = model_id
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.request_timeout = request_timeout

    def generate(self, prompt: str, stop: List[str] | None = None) -> ModelOutput:
        t0 = time.time()
        resp = self.client.responses.create(
            model=self.model_id,
            input=prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            stop=stop or None,
            timeout=self.request_timeout
        )
        latency = time.time() - t0
        text = getattr(resp, "output_text", None) or resp.output[0].content[0].text  # fallback
        usage = getattr(resp, "usage", {}) or {}
        return ModelOutput(text=text, usage=usage, latency_sec=latency)
