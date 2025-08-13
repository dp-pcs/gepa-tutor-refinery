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


def load_mmlu(subjects: list[str], split: str, n: int) -> list[MCQ]:
    """
    Load MMLU (hendrycks_test) subjects and return unified MCQ list.
    Notes:
      - Many users treat 'validation' as dev and 'test' as held-out.
      - Each subject is loaded separately; we then concatenate & sample.
    """
    from datasets import load_dataset
    pool = []
    # Use 'validation' split for dev; 'test' for test; 'train' rarely used
    hf_split = "validation" if split == "dev" else ("test" if split == "test" else "train")
    for subj in subjects:
        ds = load_dataset("cais/mmlu", subj)[hf_split]
        for ex in ds:
            # ex['question'] (str), ex['answer'] (letter "A"/"B"/"C"/"D"), ex['choices'] (list[str])
            choices = [{"label": chr(ord('A')+i), "text": t} for i, t in enumerate(ex["choices"])]
            pool.append(MCQ(
                id=f"{subj}:{ex.get('idx', len(pool))}",
                context="",  # MMLU generally has no long passage
                question=ex["question"],
                choices=choices,
                answer=ex["answer"]
            ))
    import random
    random.shuffle(pool)
    return pool[:n]


def load_truthfulqa_mc(split: str, n: int) -> list[MCQ]:
    from datasets import load_dataset
    ds = load_dataset("EleutherAI/truthful_qa_mc")["validation"]  # pool
    rows = []
    for i, ex in enumerate(ds):
        # choices may be list[str] or list[dict]; normalize
        raw_choices = ex.get("choices", [])
        if isinstance(raw_choices[0], dict):
            opts = [c.get("text", "") for c in raw_choices]
        else:
            opts = list(raw_choices)
        choices = [{"label": chr(ord('A')+j), "text": t} for j, t in enumerate(opts)]

        # gold may be 'label' ('A'..'D') or an index
        gold = ex.get("label", ex.get("answer", ex.get("correct", None)))
        if isinstance(gold, int):
            gold_letter = chr(ord('A') + gold)
        else:
            gold_letter = str(gold).strip().upper()

        rows.append(MCQ(id=f"tqa:{i}", context="", question=ex["question"], choices=choices, answer=gold_letter))
    import random; random.shuffle(rows)

    # carve dev/test from pool
    if split == "dev":   return rows[:n]
    if split == "test":  return rows[n:2*n]
    return rows[2*n:3*n]


def load_mmlu_pro(split: str, n: int) -> list[MCQ]:
    from datasets import load_dataset
    # MMLU-Pro has 10 choices (A-J) and is harder than standard MMLU
    # MMLU-Pro only has validation and test splits, no train
    if split == "train":
        # Return empty list for train split since it doesn't exist
        return []
    
    # Map split names: dev -> validation, test -> test
    if split == "dev":
        hf_split = "validation"
    elif split == "test":
        hf_split = "test"
    else:
        hf_split = split
    
    ds = load_dataset("TIGER-Lab/MMLU-Pro")[hf_split]
    items = []
    for i, ex in enumerate(ds):
        # MMLU-Pro has 10 choices labeled A-J
        choices = [{"label": chr(ord('A')+j), "text": t} for j, t in enumerate(ex["options"])]
        items.append(MCQ(id=f"mmlu_pro:{i}", context="", question=ex["question"], choices=choices, answer=ex["answer"]))
    import random; random.shuffle(items)
    return items[:n]


def load_openbookqa(split: str, n: int) -> list[MCQ]:
    from datasets import load_dataset
    ds = load_dataset("openbookqa")[split]
    pool = []
    for i, ex in enumerate(ds):
        # dataset provides: question_stem, choices (dict with text/label lists), answerKey
        choices = [{"label": label, "text": text} for label, text in zip(ex["choices"]["label"], ex["choices"]["text"])]
        pool.append(MCQ(id=f"obqa:{i}", context="", question=ex["question_stem"], choices=choices, answer=ex["answerKey"]))
    import random; random.shuffle(pool)
    return pool[:n]


def load_gpqa_diamond(split: str, n: int) -> list[MCQ]:
    """Load GPQA-Diamond dataset (extremely challenging STEM questions)"""
    from datasets import load_dataset
    ds = load_dataset("fingertap/GPQA-Diamond")["test"]  # only test split available
    pool = []
    for i, ex in enumerate(ds):
        # Parse the question format: question with a), b), c), d) options followed by A. B. C. D. mapping
        question_text = ex["question"]
        
        # Extract the main question and options
        lines = question_text.split('\n')
        main_question = lines[0].strip()
        
        # Find the options (a), b), c), d) format)
        options = []
        for line in lines[1:]:
            line = line.strip()
            if line.startswith(('a)', 'b)', 'c)', 'd)')):
                options.append(line[2:].strip())
        
        # Find the A. B. C. D. mapping (e.g., "A. d", "B. a", "C. b", "D. c")
        mapping = {}
        for line in lines:
            if line.startswith(('A.', 'B.', 'C.', 'D.')):
                parts = line.split('.')
                if len(parts) >= 2:
                    letter = parts[0].strip()
                    option_ref = parts[1].strip()
                    mapping[letter] = option_ref
        
        # Create choices in A, B, C, D format
        choices = []
        
        # Check if we have the a), b), c), d) format with mapping
        if options and mapping:
            for letter in ['A', 'B', 'C', 'D']:
                if letter in mapping:
                    option_ref = mapping[letter]
                    # Find the corresponding option text
                    if option_ref == 'a' and len(options) > 0:
                        choices.append({"label": letter, "text": options[0]})
                    elif option_ref == 'b' and len(options) > 1:
                        choices.append({"label": letter, "text": options[1]})
                    elif option_ref == 'c' and len(options) > 2:
                        choices.append({"label": letter, "text": options[2]})
                    elif option_ref == 'd' and len(options) > 3:
                        choices.append({"label": letter, "text": options[3]})
        
        # If no choices found, look for direct A. B. C. D. format
        if not choices:
            for line in lines:
                line = line.strip()
                if line.startswith(('A.', 'B.', 'C.', 'D.')):
                    parts = line.split('.')
                    if len(parts) >= 2:
                        letter = parts[0].strip()
                        choice_text = parts[1].strip()
                        choices.append({"label": letter, "text": choice_text})
        
        # Get the correct answer
        correct_answer = ex["answer"]
        

        
        pool.append(MCQ(
            id=f"gpqa_diamond:{i}",
            context="",
            question=main_question,
            choices=choices,
            answer=correct_answer
        ))
    
    import random; random.shuffle(pool)
    return pool[:n]


def load_agieval_lsat_ar(split: str, n: int) -> list[MCQ]:
    """Load AGIEval LSAT Analytical Reasoning dataset"""
    from datasets import load_dataset
    ds = load_dataset("hails/agieval-lsat-ar")["test"]  # only test split available
    pool = []
    for i, ex in enumerate(ds):
        # Parse the complex query format
        query = ex["query"]
        choices = ex["choices"]
        gold = ex["gold"][0] if ex["gold"] else 0  # gold is a list, take first element
        
        # Convert to A, B, C, D, E format
        choices_formatted = []
        for j, choice in enumerate(choices):
            choices_formatted.append({"label": chr(ord('A') + j), "text": choice})
        
        # Convert gold index to letter
        correct_answer = chr(ord('A') + gold)
        
        pool.append(MCQ(
            id=f"lsat_ar:{i}",
            context="",
            question=query,
            choices=choices_formatted,
            answer=correct_answer
        ))
    
    import random; random.shuffle(pool)
    return pool[:n]


def load_agieval_lsat_lr(split: str, n: int) -> list[MCQ]:
    """Load AGIEval LSAT Logical Reasoning dataset"""
    from datasets import load_dataset
    ds = load_dataset("hails/agieval-lsat-lr")["test"]  # only test split available
    pool = []
    for i, ex in enumerate(ds):
        query = ex["query"]
        choices = ex["choices"]
        gold = ex["gold"][0] if ex["gold"] else 0
        
        choices_formatted = []
        for j, choice in enumerate(choices):
            choices_formatted.append({"label": chr(ord('A') + j), "text": choice})
        
        correct_answer = chr(ord('A') + gold)
        
        pool.append(MCQ(
            id=f"lsat_lr:{i}",
            context="",
            question=query,
            choices=choices_formatted,
            answer=correct_answer
        ))
    
    import random; random.shuffle(pool)
    return pool[:n]


def load_agieval_sat_math(split: str, n: int) -> list[MCQ]:
    """Load AGIEval SAT Math dataset"""
    from datasets import load_dataset
    ds = load_dataset("hails/agieval-sat-math")["test"]  # only test split available
    pool = []
    for i, ex in enumerate(ds):
        query = ex["query"]
        choices = ex["choices"]
        gold = ex["gold"][0] if ex["gold"] else 0
        
        choices_formatted = []
        for j, choice in enumerate(choices):
            choices_formatted.append({"label": chr(ord('A') + j), "text": choice})
        
        correct_answer = chr(ord('A') + gold)
        
        pool.append(MCQ(
            id=f"sat_math:{i}",
            context="",
            question=query,
            choices=choices_formatted,
            answer=correct_answer
        ))
    
    import random; random.shuffle(pool)
    return pool[:n]


def load_logiqa2(split: str, n: int) -> list[MCQ]:
    """Load LogiQA 2.0 dataset (massive logical reasoning)"""
    from datasets import load_dataset
    ds = load_dataset("datatune/LogiQA2.0")
    
    # Map split names
    if split == "dev":
        hf_split = "validation"
    elif split == "test":
        hf_split = "test"
    else:
        hf_split = "train"
    
    pool = []
    for i, ex in enumerate(ds[hf_split]):
        # Parse the text field which contains JSON-like structure
        text = ex["text"]
        
        # Extract question and choices from the text
        # Format varies, but typically has question and multiple choice options
        lines = text.split('\n')
        question = ""
        choices = []
        answer = None
        
        # Simple parsing - look for question and choices
        for line in lines:
            line = line.strip()
            if line.startswith('Q:') or line.startswith('Question:'):
                question = line.split(':', 1)[1].strip()
            elif line.startswith(('A.', 'B.', 'C.', 'D.')):
                choice_text = line.split('.', 1)[1].strip()
                choice_label = line.split('.')[0]
                choices.append({"label": choice_label, "text": choice_text})
            elif line.startswith('Answer:'):
                answer = line.split(':', 1)[1].strip()
        
        # If we couldn't parse properly, skip this example
        if not question or len(choices) < 2 or not answer:
            continue
            
        pool.append(MCQ(
            id=f"logiqa2:{i}",
            context="",
            question=question,
            choices=choices,
            answer=answer
        ))
    
    import random; random.shuffle(pool)
    return pool[:n]


def load_truthfulqa_official(split: str, n: int) -> list[MCQ]:
    """Load official TruthfulQA multiple choice dataset"""
    from datasets import load_dataset
    ds = load_dataset("truthfulqa/truthful_qa", "multiple_choice")["validation"]
    
    pool = []
    for i, ex in enumerate(ds):
        question = ex["question"]
        
        # Use mc1_targets (first set of choices)
        mc1 = ex["mc1_targets"]
        choices = []
        for j, choice in enumerate(mc1["choices"]):
            choices.append({"label": chr(ord('A') + j), "text": choice})
        
        # Find correct answer (label = 1)
        correct_idx = mc1["labels"].index(1) if 1 in mc1["labels"] else 0
        correct_answer = chr(ord('A') + correct_idx)
        
        pool.append(MCQ(
            id=f"truthfulqa:{i}",
            context="",
            question=question,
            choices=choices,
            answer=correct_answer
        ))
    
    import random; random.shuffle(pool)
    
    # Carve dev/test from the pool
    if split == "dev":
        return pool[:n]
    elif split == "test":
        return pool[n:2*n]
    else:
        return pool[2*n:3*n]
