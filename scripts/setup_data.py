import argparse, json, random, pathlib, shutil, sys
from datasets import load_dataset

# Add src to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def to_unified_race(ex):
    return {
        "id": str(ex["example_id"]),
        "context": ex["article"],
        "question": ex["question"],
        "choices": [{"label": chr(ord('A')+i), "text": t} for i,t in enumerate(ex["options"])],
        "answer": ex["answer"]
    }

def to_unified_arc(ex):
    return {
        "id": str(ex["id"]),
        "context": "",
        "question": ex["question"],
        "choices": [{"label": label, "text": text} for label, text in zip(ex["choices"]["label"], ex["choices"]["text"])],
        "answer": ex["answerKey"]
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["synthetic","race","arc_easy","arc_challenge","mmlu","mmlu_pro","truthfulqa_mc","openbookqa","gpqa_diamond","agieval_lsat_ar","agieval_lsat_lr","agieval_sat_math","logiqa2","truthfulqa_official"], required=True)
    ap.add_argument("--subset", choices=["middle","high"], default="middle")
    ap.add_argument("--subjects", type=str, default="")  # comma-separated for mmlu
    ap.add_argument("--n_train", type=int, default=60)
    ap.add_argument("--n_dev", type=int, default=20)
    ap.add_argument("--n_test", type=int, default=20)
    ap.add_argument("--out_dir", type=str, default="data")
    args = ap.parse_args()

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if args.dataset == "synthetic":
        # Just copy from sample_data
        import shutil, pathlib as p
        base = p.Path("sample_data")
        shutil.copy(base / "synthetic_train.jsonl", out / "train.jsonl")
        shutil.copy(base / "synthetic_dev.jsonl", out / "dev.jsonl")
        shutil.copy(base / "synthetic_test.jsonl", out / "test.jsonl")
        print("Wrote synthetic splits to", out)
        return

    if args.dataset == "race":
        ds_train = load_dataset("EleutherAI/race", args.subset)["train"]
        ds_dev = load_dataset("EleutherAI/race", args.subset)["validation"]
        # sample
        train = [to_unified_race(ex) for ex in ds_train.select(range(min(args.n_train, len(ds_train))))]
        dev = [to_unified_race(ex) for ex in ds_dev.select(range(min(args.n_dev, len(ds_dev))))]
        test = [to_unified_race(ex) for ex in ds_dev.select(range(min(args.n_test, len(ds_dev))))]  # reuse val for test in small runs
    elif args.dataset == "mmlu":
        from datasets import load_dataset
        subjects = [s.strip() for s in args.subjects.split(",") if s.strip()]
        if not subjects:
            # default to tough but relevant subjects
            subjects = ["high_school_physics","high_school_chemistry","high_school_biology",
                        "college_mathematics","formal_logic"]
        def to_unified_mmlu(ex, subj, idx):
            return {
                "id": f"{subj}:{idx}",
                "context": "",
                "question": ex["question"],
                "choices": [{"label": chr(ord('A')+i), "text": t} for i, t in enumerate(ex["choices"])],
                "answer": ex["answer"]
            }
        # build splits from MMLU's validation/test
        train, dev, test = [], [], []
        for subj in subjects:
            ds = load_dataset("cais/mmlu", subj)
            for i, ex in enumerate(ds["validation"]):
                dev.append(to_unified_mmlu(ex, subj, i))
            for i, ex in enumerate(ds["test"]):
                test.append(to_unified_mmlu(ex, subj, i))
        # sample to requested sizes
        import random
        random.shuffle(dev); random.shuffle(test)
        dev = dev[:args.n_dev]; test = test[:args.n_test]
        # train is optional; keep small or empty
    elif args.dataset == "mmlu_pro":
        from datasets import load_dataset
        ds = load_dataset("TIGER-Lab/MMLU-Pro")
        items = []
        for i, ex in enumerate(ds["validation"]):
            choices = [{"label": chr(ord('A')+j), "text": t} for j, t in enumerate(ex["options"])]
            items.append({
                "id": f"mmlu_pro:{i}",
                "context": "",
                "question": ex["question"],
                "choices": choices,
                "answer": ex["answer"]
            })
        import random
        random.shuffle(items)
        # MMLU-Pro has validation/test, carve dev/test
        dev = items[:args.n_dev]
        test = items[args.n_dev:args.n_dev + args.n_test]
        train = []  # no train split for MMLU-Pro

    elif args.dataset == "truthfulqa_mc":
        from datasets import load_dataset
        ds = load_dataset("EleutherAI/truthful_qa_mc")["validation"]
        items = []
        for i, ex in enumerate(ds):
            choices = [{"label": chr(ord('A')+j), "text": t} for j, t in enumerate(ex["choices"])]
            items.append({
                "id": f"tqa:{i}",
                "context": "",
                "question": ex["question"],
                "choices": choices,
                "answer": ex["label"]
            })
        import random
        random.shuffle(items)
        # carve dev/test from the pool
        dev = items[:args.n_dev]
        test = items[args.n_dev:args.n_dev + args.n_test]
        train = []  # no train split for TruthfulQA

    elif args.dataset == "openbookqa":
        from datasets import load_dataset
        ds = load_dataset("openbookqa")
        items = []
        for i, ex in enumerate(ds["validation"]):
            choices = [{"label": label, "text": text} for label, text in zip(ex["choices"]["label"], ex["choices"]["text"])]
            items.append({
                "id": f"obqa:{i}",
                "context": "",
                "question": ex["question_stem"],
                "choices": choices,
                "answer": ex["answerKey"]
            })
        import random
        random.shuffle(items)
        # OpenBookQA has validation/test, carve dev/test
        dev = items[:args.n_dev]
        test = items[args.n_dev:args.n_dev + args.n_test]
        train = []  # no train split for OpenBookQA

    elif args.dataset == "gpqa_diamond":
        from data_loader import load_gpqa_diamond
        items = []
        for i in range(args.n_dev + args.n_test):
            items.append(load_gpqa_diamond("test", 1)[0])  # Load one at a time to avoid duplicates
        import random; random.shuffle(items)
        # Convert MCQ objects to dictionaries
        dev = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[:args.n_dev]]
        test = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[args.n_dev:args.n_dev + args.n_test]]
        train = []

    elif args.dataset == "agieval_lsat_ar":
        from data_loader import load_agieval_lsat_ar
        items = []
        for i in range(args.n_dev + args.n_test):
            items.append(load_agieval_lsat_ar("test", 1)[0])
        import random; random.shuffle(items)
        # Convert MCQ objects to dictionaries
        dev = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[:args.n_dev]]
        test = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[args.n_dev:args.n_dev + args.n_test]]
        train = []

    elif args.dataset == "agieval_lsat_lr":
        from data_loader import load_agieval_lsat_lr
        items = []
        for i in range(args.n_dev + args.n_test):
            items.append(load_agieval_lsat_lr("test", 1)[0])
        import random; random.shuffle(items)
        # Convert MCQ objects to dictionaries
        dev = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[:args.n_dev]]
        test = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[args.n_dev:args.n_dev + args.n_test]]
        train = []

    elif args.dataset == "agieval_sat_math":
        from data_loader import load_agieval_sat_math
        items = []
        for i in range(args.n_dev + args.n_test):
            items.append(load_agieval_sat_math("test", 1)[0])
        import random; random.shuffle(items)
        # Convert MCQ objects to dictionaries
        dev = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[:args.n_dev]]
        test = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in items[args.n_dev:args.n_dev + args.n_test]]
        train = []

    elif args.dataset == "logiqa2":
        from data_loader import load_logiqa2
        dev_raw = load_logiqa2("dev", args.n_dev)
        test_raw = load_logiqa2("test", args.n_test)
        train_raw = load_logiqa2("train", args.n_train)
        # Convert MCQ objects to dictionaries
        dev = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in dev_raw]
        test = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in test_raw]
        train = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in train_raw]

    elif args.dataset == "truthfulqa_official":
        from data_loader import load_truthfulqa_official
        dev_raw = load_truthfulqa_official("dev", args.n_dev)
        test_raw = load_truthfulqa_official("test", args.n_test)
        train_raw = load_truthfulqa_official("train", args.n_train)
        # Convert MCQ objects to dictionaries
        dev = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in dev_raw]
        test = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in test_raw]
        train = [{"id": item.id, "context": item.context, "question": item.question, "choices": item.choices, "answer": item.answer} for item in train_raw]

    else:
        config = "ARC-Easy" if args.dataset == "arc_easy" else "ARC-Challenge"
        ds_train = load_dataset("allenai/ai2_arc", config)["train"]
        ds_val = load_dataset("allenai/ai2_arc", config)["validation"]
        train = [to_unified_arc(ex) for ex in ds_train.select(range(min(args.n_train, len(ds_train))))]
        dev = [to_unified_arc(ex) for ex in ds_val.select(range(min(args.n_dev, len(ds_val))))]
        test = [to_unified_arc(ex) for ex in ds_val.select(range(min(args.n_test, len(ds_val))))]

    write_jsonl(out / "train.jsonl", train)
    write_jsonl(out / "dev.jsonl", dev)
    write_jsonl(out / "test.jsonl", test)
    print("Wrote splits to", out)

if __name__ == "__main__":
    main()
