import argparse, json, random, pathlib, shutil
from datasets import load_dataset

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
        "choices": [{"label": c["label"], "text": c["text"]} for c in ex["choices"]],
        "answer": ex["answerKey"]
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["synthetic","race","arc_easy","arc_challenge"], required=True)
    ap.add_argument("--subset", choices=["middle","high"], default="middle")
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
