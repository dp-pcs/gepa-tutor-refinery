from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelOutput:
    text: str
    usage: Dict[str, Any]
    latency_sec: float

class Provider(ABC):
    @abstractmethod
    def generate(self, prompt: str, stop: list[str] | None = None) -> ModelOutput:
        ...
