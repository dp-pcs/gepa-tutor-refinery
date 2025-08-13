import time
from .provider import Provider, ModelOutput

class AlwaysAProvider(Provider):
    def generate(self, prompt, stop=None):
        t0 = time.time()
        return ModelOutput(
            text="Answer: A", 
            usage={"output_tokens": 2}, 
            latency_sec=time.time() - t0
        )
