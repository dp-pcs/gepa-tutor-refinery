import json, pathlib
from typing import List, Dict, Any
from .models.provider import Provider
from .utils import write_jsonl

REFLECTION_PROMPT = """You are improving a system prompt for a multiple-choice tutor.
You will see FAILED EXAMPLES: each includes (context, question, choices, your_answer, correct_answer).

1) Diagnose recurring failure modes as general rules (not per-example tips).
2) Propose {num_edits} prompt edits. Each edit must be:
   - Self-contained (can be appended to the base prompt)
   - Max 5 lines, imperative, testable
   - Include any verification/check steps
3) For each edit, state which failure modes it addresses.

Return **valid JSON** only in this schema:
{{
  "rules": ["..."],
  "edits": [
     {{"name":"A","text":"<edit text>","why":"<which failures it fixes>"}}
  ]
}}"""

def build_fail_snippet(row: Dict[str, Any]) -> str:
    ctx = row.get("context","")
    q = row.get("question","")
    ch = row.get("choices","")
    your = row.get("answer_pred","")
    gold = row.get("answer_gold","")
    return f"Context: {ctx}\nQuestion: {q}\nChoices: {ch}\nYour answer: {your}\nCorrect answer: {gold}"

def reflect(provider: Provider, failed_rows: List[Dict[str, Any]], num_edits: int, out_path: str, base_prompt: str) -> Dict[str, Any]:
    # Construct reflection prompt
    snippets = []
    for r in failed_rows:
        # compact choices
        ch_txt = " ".join([f"{c['label']}. {c['text']}" for c in r.get("choices_parsed", [])]) if r.get("choices_parsed") else ""
        s = {
            "context": r.get("context",""),
            "question": r.get("question",""),
            "choices": ch_txt,
            "answer_pred": r.get("answer_pred",""),
            "answer_gold": r.get("answer_gold",""),
        }
        snippets.append(s)
    # Truncate to a reasonable size
    snippets = snippets[:50]
    fail_block = json.dumps(snippets, ensure_ascii=False, indent=2)
    prompt = REFLECTION_PROMPT.format(num_edits=num_edits) + f"""

BASE PROMPT:
---
{base_prompt}
---
FAILED EXAMPLES (JSON):
{fail_block}
"""
    result = provider.generate(prompt)
    # Try parse JSON
    try:
        data = json.loads(result.text)
    except Exception:
        data = {"rules": [], "edits": []}
    # Save raw + parsed
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt, "raw_response": result.text, "parsed": data}, f, ensure_ascii=False, indent=2)
    return data
