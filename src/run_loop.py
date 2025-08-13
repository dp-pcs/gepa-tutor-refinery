import argparse, yaml, pathlib, shutil, time, json, random
from typing import List, Dict, Any
from dotenv import load_dotenv
from .utils import ensure_dir, seed_everything, timestamp, write_jsonl
from .evaluator import run_eval, EvalResult, Example
from .reflect_and_edit import reflect
from .pareto import pareto_frontier
from .models.mock_client import MockProvider
from .models.always_a_client import AlwaysAProvider
try:
    from .models.openai_client import OpenAIProvider
except Exception:
    OpenAIProvider = None
try:
    from .models.anthropic_client import AnthropicProvider
except Exception:
    AnthropicProvider = None

from .data_loader import load_synthetic, load_race, load_arc, load_mmlu, load_mmlu_pro, load_truthfulqa_mc, load_openbookqa, load_gpqa_diamond, load_agieval_lsat_ar, load_agieval_lsat_lr, load_agieval_sat_math, load_logiqa2, load_truthfulqa_official
from pathlib import Path

def make_provider(cfg):
    prov = cfg["model"]["provider"]
    mid = cfg["model"]["model_id"]
    temp = cfg["model"]["temperature"]
    max_toks = cfg["model"]["max_output_tokens"]
    tout = cfg["model"]["request_timeout"]
    if prov == "mock":
        return MockProvider()
    if prov == "always_a":
        return AlwaysAProvider()
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
    elif name == "mmlu":
        # Default to challenging subjects if not specified
        subjects = ["high_school_physics", "high_school_chemistry", "high_school_biology", 
                   "college_mathematics", "formal_logic"]
        items = load_mmlu(subjects, split, n)
    elif name == "mmlu_pro":
        items = load_mmlu_pro(split, n)
    elif name == "truthfulqa_mc":
        items = load_truthfulqa_mc(split, n)
    elif name == "openbookqa":
        items = load_openbookqa(split, n)
    elif name == "gpqa_diamond":
        items = load_gpqa_diamond(split, n)
    elif name == "agieval_lsat_ar":
        items = load_agieval_lsat_ar(split, n)
    elif name == "agieval_lsat_lr":
        items = load_agieval_lsat_lr(split, n)
    elif name == "agieval_sat_math":
        items = load_agieval_sat_math(split, n)
    elif name == "logiqa2":
        items = load_logiqa2(split, n)
    elif name == "truthfulqa_official":
        items = load_truthfulqa_official(split, n)
    else:
        raise ValueError(f"Unknown dataset: {name}")
    # Cast to evaluator.Example
    return [Example(id=ex.id, context=ex.context, question=ex.question, choices=ex.choices, answer=ex.answer) for ex in items[:n]]

def save_prompt(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default="configs/config.yaml")
    ap.add_argument("--mode", type=str, choices=["baseline","self_refine","gepa","distill_from_self_refine","hybrid"], default="baseline")
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

    elif args.mode == "distill_from_self_refine":
        # Distill Self-Refine behavior into a single-call prompt (TRAINING TIME ONLY)
        print("Running distillation from Self-Refine...")
        
        # TRAINING PHASE: Run Self-Refine on dev to collect correct examples and their revisions
        print("Phase 1: Collecting Self-Refine traces...")
        res_dev = run_eval(provider, base_prompt, dev, strategy="self_refine", self_refine_steps=cfg["evaluation"]["self_refine_steps"], out_dir=str(out_dir / "training" / "self_refine"))
        
        # Load Self-Refine records to analyze successful corrections
        dev_records = [json.loads(l) for l in open(out_dir / "training" / "self_refine" / "records.jsonl", "r")]
        correct_examples = [r for r in dev_records if r["correct"] == 1]
        
        print(f"Collected {len(correct_examples)} correct examples for distillation")
        
        # TRAINING PHASE: Reflect on successful corrections to extract rules
        print("Phase 2: Extracting distillation rules...")
        distill_prompt = f"""Analyze these successful Self-Refine corrections and extract the implicit rules:

EXAMPLES:
{json.dumps(correct_examples[:10], indent=2)}

What rules did the model implicitly follow to achieve 100% accuracy? Produce 3-5 concise, enforceable edits (≤3 lines each) that could be appended to the base prompt.

Focus on:
- Error detection patterns
- Correction strategies  
- Format enforcement
- Reasoning improvements

IMPORTANT: Preserve the final-line format requirement. Output only the rules, one per line, starting with "- "."""
        
        distill_result = provider.generate(distill_prompt)
        
        # TRAINING PHASE: Build prompt variants by appending distilled rules
        print("Phase 3: Building prompt variants...")
        distilled_rules = distill_result.text.strip()
        
        # Create 2-4 variants with different rule combinations
        rules_lines = [line.strip() for line in distilled_rules.split('\n') if line.strip().startswith('-')]
        variants = []
        
        for i in range(min(3, len(rules_lines))):
            variant_rules = rules_lines[:i+1]
            variant_prompt = base_prompt + "\n\nDISTILLED RULES:\n" + "\n".join(variant_rules)
            
            vdir = out_dir / "training" / f"variant_{chr(ord('A')+i)}"
            save_prompt(vdir / "prompt.txt", variant_prompt)
            
            # Evaluate variant on dev (single call only)
            res = run_eval(provider, variant_prompt, dev, strategy="baseline", out_dir=str(vdir / "dev"))
            variants.append({
                "name": chr(ord('A')+i),
                "accuracy": res.accuracy,
                "avg_tokens_out": res.avg_tokens_out if res.avg_tokens_out is not None else 0.0,
                "avg_latency_sec": res.avg_latency_sec,
                "prompt_path": str(vdir / "prompt.txt"),
                "rules": variant_rules
            })
        
        # TRAINING PHASE: Pareto-select best variant
        print("Phase 4: Selecting best variant...")
        frontier = pareto_frontier(variants, x_key="avg_tokens_out", y_key="accuracy")
        best = sorted(frontier, key=lambda r: (-r["accuracy"], r["avg_tokens_out"]))[0] if frontier else variants[0]
        
        # Save distillation results
        with open(out_dir / "training" / "distillation_results.json", "w") as f:
            json.dump({
                "distilled_rules": distilled_rules,
                "variants": variants,
                "pareto_frontier": frontier,
                "best_variant": best
            }, f, indent=2)
        
        # INFERENCE PHASE: Evaluate best distilled prompt on test (single call only)
        print("Phase 5: Evaluating distilled prompt on test...")
        best_prompt = Path(best["prompt_path"]).read_text(encoding="utf-8")
        res_test = run_eval(provider, best_prompt, test, strategy="baseline", out_dir=str(out_dir / "test"))
        
        # Calculate training overhead
        training_tokens = sum([
            distill_result.usage.get("total_tokens", 0) if hasattr(distill_result, 'usage') else 0
        ])
        
        summary = {
            "mode": "distill_from_self_refine",
            "dev_accuracy": best["accuracy"],
            "dev_avg_tokens_out": best["avg_tokens_out"],
            "dev_avg_latency_sec": best["avg_latency_sec"],
            "test_accuracy": res_test.accuracy,
            "test_avg_tokens_out": res_test.avg_tokens_out,
            "test_avg_latency_sec": res_test.avg_latency_sec,
            "training_tokens_total": training_tokens,
            "best_variant": best["name"],
            "distilled_rules": best["rules"]
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

    elif args.mode == "hybrid":
        # Hybrid: SR → GEPA Review (2-stage chain)
        print("Running hybrid mode: SR → GEPA Review...")
        
        # Run hybrid evaluation on both dev and test
        res_dev = run_eval(provider, base_prompt, dev, strategy="hybrid", out_dir=str(out_dir / "dev"))
        res_test = run_eval(provider, base_prompt, test, strategy="hybrid", out_dir=str(out_dir / "test"))
        
        summary = {
            "mode": "hybrid",
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

if __name__ == "__main__":
    main()
