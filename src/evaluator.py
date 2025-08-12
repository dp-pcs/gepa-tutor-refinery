import time, pathlib, json, statistics
from dataclasses import dataclass
from typing import List, Dict, Any
from .models.provider import Provider
from .utils import ensure_dir, write_jsonl, parse_answer_letter

@dataclass
class Example:
    id: str
    context: str
    question: str
    choices: list[dict]
    answer: str

@dataclass
class EvalResult:
    accuracy: float
    avg_tokens_out: float | None
    avg_latency_sec: float
    records_path: str

def render_mcq_prompt(base_prompt: str, ex: Example) -> str:
    choices_text = "\n".join([f"{c['label']}. {c['text']}" for c in ex.choices])
    ctx = f"PASSAGE: {ex.context}\n" if ex.context else ""
    return f"""{base_prompt}

{ctx}QUESTION: {ex.question}
CHOICES:
{choices_text}

Follow the format exactly. End with 'Answer: <LETTER>'."""

def run_eval(provider: Provider, base_prompt: str, examples: List[Example], strategy: str = "baseline", self_refine_steps: int = 1, out_dir: str = "runs/tmp") -> EvalResult:
    ensure_dir(out_dir)
    rows = []
    correct = 0
    tokens_list, latency_list = [], []
    for ex in examples:
        prompt = render_mcq_prompt(base_prompt, ex)
        if strategy == "baseline":
            result = provider.generate(prompt)
            answer = parse_answer_letter(result.text)
        elif strategy == "self_refine":
            # 1) initial
            r1 = provider.generate(prompt)
            # 2) critique & revise
            crit = f"""You earlier answered an MCQ. Here is your answer:
---
{r1.text}
---
Critique briefly, then produce a corrected answer with the exact final line 'Answer: <LETTER>'. Keep total <=100 tokens."""
            r2 = provider.generate(crit)
            result = r2
            answer = parse_answer_letter(result.text)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        is_correct = 1 if (answer == ex.answer) else 0
        correct += is_correct
        tokens_out = None
        if isinstance(result.usage, dict):
            # try common fields
            tokens_out = result.usage.get("output_tokens") or result.usage.get("output_tokens", None)
        rows.append({
            "id": ex.id,
            "answer_gold": ex.answer,
            "answer_pred": answer,
            "correct": is_correct,
            "latency_sec": result.latency_sec,
            "usage": result.usage,
            "raw_text": result.text
        })
        latency_list.append(result.latency_sec)
        if tokens_out is not None:
            tokens_list.append(tokens_out)
    acc = correct / len(examples) if examples else 0.0
    avg_tokens = statistics.mean(tokens_list) if tokens_list else None
    avg_latency = statistics.mean(latency_list) if latency_list else 0.0
    rec_path = pathlib.Path(out_dir) / "records.jsonl"
    write_jsonl(rec_path, rows)
    return EvalResult(accuracy=acc, avg_tokens_out=avg_tokens, avg_latency_sec=avg_latency, records_path=str(rec_path))
