# 2-Hour Tutor Prompt Refinery (GEPA-style)

**Elevator pitch:** A small, transparent **prompt-refinery pipeline** for AI tutoring.
It runs a **GEPA-style loop** — *run → reflect on failures → propose prompt edits → A/B test → Pareto-select → iterate* —
to maximize **learning accuracy per minute** while controlling **cost/latency**.

This repo is framework-agnostic and uses **public datasets** (RACE / ARC) or a **synthetic MCQ set**.
It’s reproducible, versioned, and easy to fork into your own tutor flows.

## Why this is interesting
- Shows a **measurable, auditable** way to continuously improve tutor prompts (not weights).
- Keeps only **Pareto-optimal** variants: more accurate *and/or* cheaper/faster.
- Produces **prompt diffs** and **failure→fix** narratives stakeholders can read.

## Methods compared
- **Baseline** (single-shot tutor prompt)
- **Self-Refine** (iterative self-feedback; prompt-only)
- **GEPA-style loop** (reflect → edit prompts → evaluate → Pareto select)
- *(Optional)* **DSPy MIPROv2** baseline — see notes; not required to run this repo.

## Datasets (pick one)
- **RACE** (reading comprehension MCQ; middle/high school). Auto-graded accuracy.
- **ARC** (grade-school science MCQ). Auto-graded accuracy.
- **Synthetic MCQ** (included) for fully offline smoke tests.

> ⚠️ Licensing: Use the Hugging Face dataset cards to confirm terms for your use case.

## Quickstart

```bash
# 0) Python 3.10+ recommended
python -V

# 1) Create venv and install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) Set API keys (optional; otherwise the mock model is used)
export OPENAI_API_KEY=...     # or
export ANTHROPIC_API_KEY=...

# 3) Prepare a small split (RACE/ARC) or use the synthetic set
python scripts/setup_data.py --dataset synthetic --n_train 30 --n_dev 10 --n_test 10
# For RACE (requires internet to download via datasets):
# python scripts/setup_data.py --dataset race --subset middle --n_train 60 --n_dev 20 --n_test 20
# For ARC (Easy):
# python scripts/setup_data.py --dataset arc_easy --n_train 60 --n_dev 20 --n_test 20

# 4) Run baselines
python src/run_loop.py --config configs/config.yaml --mode baseline
python src/run_loop.py --config configs/config.yaml --mode self_refine

# 5) Run GEPA loop (2 iterations by default)
python src/run_loop.py --config configs/config.yaml --mode gepa

# 6) Make a report (tables + Pareto chart)
python scripts/make_report.py --runs_dir runs --out report/results.md
```

Artifacts appear under `runs/<timestamp>/` with configs, prompts, per-sample logs, reflections, and figures.

## Config
See `configs/config.yaml` — select dataset, model provider, metrics, and GEPA params.

## Result reading
- `summary.csv` → pass@1 accuracy, avg tokens, avg latency.
- `pareto.csv` and `pareto.png` → non-dominated prompt variants (accuracy vs avg tokens).
- `prompt_diffs/` → before/after diffs.
- `examples_failed.jsonl` → failure traces used for reflections.

## Safety & privacy
- Default uses **public datasets** or **synthetic** examples — no student data.
- If later using real logs: anonymize, use held-out sets, and follow FERPA/COPPA as applicable.

## Citation
If you reference this repo, please cite the GEPA paper and dataset sources.

