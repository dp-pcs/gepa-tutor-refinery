import random, time
from .provider import Provider, ModelOutput

class MockProvider(Provider):
    def __init__(self, *args, **kwargs):
        pass

    def generate(self, prompt: str, stop=None) -> ModelOutput:
        # Very naive: pick a random letter A-D and echo a short explanation.
        t0 = time.time()
        letter = random.choice(['A','B','C','D'])
        text = f"Reasoning: (mock) I considered options.\nAnswer: {letter}"
        return ModelOutput(text=text, usage={"output_tokens": len(text.split())}, latency_sec=time.time() - t0)
