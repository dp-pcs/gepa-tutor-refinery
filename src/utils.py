import os, json, re, time, uuid, pathlib, difflib, random
from typing import Any, Dict, List

def ensure_dir(p: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_jsonl(path: str | pathlib.Path, rows: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def parse_answer_letter(text: str) -> str | None:
    # extract final 'Answer: X' or single capital letter A-D on a labeled line
    m = re.search(r"Answer\s*:\s*([A-D])\b", text.strip(), flags=re.IGNORECASE)
    if m: return m.group(1).upper()
    # fallback: last capital letter A-D in text
    m2 = re.findall(r"\b([A-D])\b", text)
    if m2: return m2[-1].upper()
    return None

def diff_text(a: str, b: str) -> str:
    return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), lineterm=""))

def timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")

def seed_everything(seed: int):
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
