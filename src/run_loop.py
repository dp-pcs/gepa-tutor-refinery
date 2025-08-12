import argparse, yaml, pathlib, shutil, time, json, random
from typing import List, Dict, Any
from .utils import ensure_dir, seed_everything, timestamp, write_jsonl
from .evaluator import run_eval, EvalResult, Example
from .reflect_and_edit import reflect
from .pareto import pareto_frontier
from .models.mock_client import MockProvider
try:
    from .models.openai_client import OpenAIProvider
except Exception:
    OpenAIProvider = None
try:
    from .models.anthropic_client import AnthropicProvider
except Exception:
    AnthropicProvider = None

from .data_loader import load_synthetic, load_race, load_arc
from pathlib import Path

def make_provider(cfg):
    prov = cfg["model"]["provider"]
    mid = cfg["model"]["model_id"]
    temp = cfg["model"]["temperature"]
    max_toks = cfg["model"]["max_output_tokens"]
    tout = cfg["model"]["request_timeout"]
    if prov == "mock":
        return MockProvider()
    if prov == "openai" and OpenAIProvider is not None:
        return OpenAIProvider(model_id=mid, temperature=temp, max_output_tokens=max_toks, request_timeout=tout)
    if prov == "anthropic" and AnthropicProvider is not None:
        return AnthropicProvider(model_id=mid, temperature=temp, max_output_tokens=max_toks, request_timeout=tout)
    raise ValueError(f"Unknown or unavailable provider: {prov}")

def load_split(cfg, split):
    name = cfg["dataset"]["name"]
    n = cfg["dataset"][f"n_{split}"]
    if name == "synthetic":
        path = Path("sample_data") / f"synthetic_{split}.jsonl"
        items = load_synthetic(path)
    elif name == "race":
        subset = cfg["dataset"]["subset"]
        items = load_race(split, subset, n)
    elif name == "arc_easy":
        items = load_arc(split, "easy", n)
    elif name == "arc_challenge":
        items = load_arc(split, "challenge", n)
    else:
        raise ValueError(f"Unknown dataset: {name}")
    # Cast to evaluator.Example
    return [Example(id=ex.id, context=ex.context, question=ex.question, choices=ex.choices, answer=ex.answer) for ex in items[:n]]

def save_prompt(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default="configs/config.yaml")
    ap.add_argument("--mode", type=str, choices=["baseline","self_refine","gepa"], default="baseline")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    seed_everything(cfg.get("seed", 42))

    runs_dir = Path(cfg["logging"]["runs_dir"])
    run_id = timestamp() + f"_{args.mode}"
    out_dir = runs_dir / run_id
    ensure_dir(out_dir)

    base_prompt = Path("src/base_tutor_prompt.txt").read_text(encoding="utf-8")
    save_prompt(out_dir / "base_prompt.txt", base_prompt)

    provider = make_provider(cfg)

    train = load_split(cfg, "train")
    dev = load_split(cfg, "dev")
    test = load_split(cfg, "test")

    if args.mode in ["baseline", "self_refine"]:
        strat = "baseline" if args.mode=="baseline" else "self_refine"
        res_dev = run_eval(provider, base_prompt, dev, strategy=strat, self_refine_steps=cfg["evaluation"]["self_refine_steps"], out_dir=str(out_dir / "dev"))
        res_test = run_eval(provider, base_prompt, test, strategy=strat, self_refine_steps=cfg["evaluation"]["self_refine_steps"], out_dir=str(out_dir / "test"))
        summary = {
            "mode": args.mode,
            "dev_accuracy": res_dev.accuracy,
            "dev_avg_tokens_out": res_dev.avg_tokens_out,
            "dev_avg_latency_sec": res_dev.avg_latency_sec,
            "test_accuracy": res_test.accuracy,
            "test_avg_tokens_out": res_test.avg_tokens_out,
            "test_avg_latency_sec": res_test.avg_latency_sec,
        }
        with open(out_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        print("Wrote", out_dir)

    elif args.mode == "gepa":
        # Round 0: baseline on dev to collect failures
        base_dev = run_eval(provider, base_prompt, dev, strategy="baseline", out_dir=str(out_dir / "round0" / "dev"))
        # Load records; enrich with question data for reflection
        dev_records = [json.loads(l) for l in open(out_dir / "round0" / "dev" / "records.jsonl", "r")]
        # enrich with text to reflect on (choices, etc.)
        enriched = []
        for ex, row in zip(dev, dev_records):
            row["context"] = ex.context
            row["question"] = ex.question
            row["choices_parsed"] = ex.choices
            enriched.append(row)
        failed = [r for r in enriched if r["correct"] == 0]
        # Reflect to propose edits
        ge_cfg = cfg["gepa"]
        data = reflect(provider, failed_rows=failed[:ge_cfg["num_reflection_examples"]], num_edits=ge_cfg["num_edits"], out_path=str(out_dir / "round1" / "reflection.json"), base_prompt=base_prompt)
        edits = data.get("edits", [])
        # Materialize variants
        variants = []
        for i, e in enumerate(edits):
            name = e.get("name", chr(ord('A')+i))
            text = e.get("text","").strip()
            if not text: 
                continue
            variant_prompt = base_prompt + "\n\n" + text
            vdir = out_dir / "round1" / f"variant_{name}"
            save_prompt(vdir / "prompt.txt", variant_prompt)
            res = run_eval(provider, variant_prompt, dev, strategy="baseline", out_dir=str(vdir / "dev"))
            variants.append({
                "name": name,
                "accuracy": res.accuracy,
                "avg_tokens_out": res.avg_tokens_out if res.avg_tokens_out is not None else 0.0,
                "avg_latency_sec": res.avg_latency_sec,
                "prompt_path": str(vdir / "prompt.txt")
            })
        # Pareto filter
        frontier = pareto_frontier(variants, x_key=cfg["gepa"]["pareto_metric_x"], y_key=cfg["gepa"]["pareto_metric_y"])
        with open(out_dir / "round1" / "variants.json", "w") as f:
            json.dump({"variants": variants, "pareto": frontier}, f, indent=2)
        # Choose best by accuracy then tokens
        best = sorted(frontier, key=lambda r: (-r["accuracy"], r["avg_tokens_out"]))[0] if frontier else (sorted(variants, key=lambda r: (-r["accuracy"]))[0] if variants else None)
        # Evaluate on test
        if best:
            prompt_text = Path(best["prompt_path"]).read_text(encoding="utf-8")
            res_test = run_eval(provider, prompt_text, test, strategy="baseline", out_dir=str(out_dir / "round1" / "test"))
            summary = {
                "mode": "gepa",
                "round1_best": best,
                "test_accuracy": res_test.accuracy,
                "test_avg_tokens_out": res_test.avg_tokens_out,
                "test_avg_latency_sec": res_test.avg_latency_sec,
            }
            with open(out_dir / "summary.json", "w") as f:
                json.dump(summary, f, indent=2)
        print("Wrote", out_dir)

if __name__ == "__main__":
    main()
