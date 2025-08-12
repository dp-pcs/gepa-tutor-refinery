import json, random, pathlib
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class MCQ:
    id: str
    context: str
    question: str
    choices: list[dict]
    answer: str

def load_synthetic(split_dir: pathlib.Path) -> list[MCQ]:
    path = split_dir
    items = []
    for line in open(path, "r", encoding="utf-8"):
        ex = json.loads(line)
        items.append(MCQ(id=ex["id"], context=ex.get("context",""), question=ex["question"],
                         choices=ex["choices"], answer=ex["answer"]))
    return items

def load_race(split: str, subset: str, n: int) -> list[MCQ]:
    # Requires: datasets
    from datasets import load_dataset
    ds = load_dataset("EleutherAI/race", subset)[split]
    # Unify
    pool = []
    for ex in ds:
        choices = [{"label": chr(ord('A')+i), "text": t} for i, t in enumerate(ex["options"])]
        pool.append(MCQ(id=str(ex["example_id"]), context=ex["article"], question=ex["question"],
                        choices=choices, answer=ex["answer"]))
    random.shuffle(pool)
    return pool[:n]

def load_arc(split: str, difficulty: str, n: int) -> list[MCQ]:
    # Requires: datasets
    from datasets import load_dataset
    config = "ARC-Easy" if difficulty == "easy" else "ARC-Challenge"
    ds = load_dataset("allenai/ai2_arc", config)[split]
    pool = []
    for ex in ds:
        choices = [{"label": c["label"], "text": c["text"]} for c in ex["choices"]]
        # ARC has no context passage, just question + choices
        pool.append(MCQ(id=str(ex["id"]), context="", question=ex["question"],
                        choices=choices, answer=ex["answerKey"]))
    random.shuffle(pool)
    return pool[:n]
