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
    # Strict: require explicit 'Answer: <LETTER>' with A-J support
    # No fallback to "last capital letter." If the model doesn't follow the format, it gets scored wrong.
    m = re.search(r"(?im)^\s*Answer\s*:\s*([A-J])\b", text)
    return m.group(1).upper() if m else None

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
