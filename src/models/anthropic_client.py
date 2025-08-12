import os, time
from typing import Dict, Any, List
from .provider import Provider, ModelOutput
import anthropic

class AnthropicProvider(Provider):
    def __init__(self, model_id: str, temperature: float = 0.2, max_output_tokens: int = 256, request_timeout: int = 60):
        self.client = anthropic.Anthropic()
        self.model_id = model_id
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.request_timeout = request_timeout

    def generate(self, prompt: str, stop: List[str] | None = None) -> ModelOutput:
        t0 = time.time()
        msg = self.client.messages.create(
            model=self.model_id,
            max_tokens=self.max_output_tokens,
            temperature=self.temperature,
            messages=[{"role":"user","content":prompt}],
            stop_sequences=stop or None,
            timeout=self.request_timeout
        )
        latency = time.time() - t0
        # Concatenate text parts
        text = "".join([b.text for b in msg.content if hasattr(b, "text")])
        usage = {"input_tokens": getattr(msg.usage, "input_tokens", None),
                 "output_tokens": getattr(msg.usage, "output_tokens", None)}
        return ModelOutput(text=text, usage=usage, latency_sec=latency)
