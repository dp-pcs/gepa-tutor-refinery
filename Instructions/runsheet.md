# Evaluation Run Sheet – [Phase Name]

## Instructions
- Run **one dataset at a time**.
- For each method (Baseline, Self-Refine, GEPA):
  1. Record **Dev Accuracy** and **Test Accuracy** (%)
  2. Record **Tokens/Q** (average total tokens per question, incl. all calls for SR)
  3. Record **TPC** (tokens per correct)
  4. Record **$100C** (optional – cost per 100 correct)
  5. Add quick **Notes** (format issues, SR wins, GEPA variant found, etc.)

---

| Dataset            | Method       | Acc Dev | Acc Test | Tokens/Q | TPC   | $100C  | Notes |
|--------------------|--------------|---------|----------|----------|-------|--------|-------|
| **GPQA-Diamond**   | Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |
| **MMLU-Pro**       | Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |
| **AGIEval LSAT-AR** | Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |
| **AGIEval LSAT-LR** | Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |
| **AGIEval SAT-Math**| Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |
| **LogiQA 2.0**     | Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |
| **MedMCQA**        | Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |
| **TruthfulQA-MC**  | Baseline     |         |          |          |       |        |       |
|                    | Self-Refine  |         |          |          |       |        |       |
|                    | GEPA         |         |          |          |       |        |       |

---

## Key to Columns
- **Acc Dev/Test** – Accuracy % on dev/test
- **Tokens/Q** – Average total tokens per question (including both input/output tokens and all calls for SR)
- **TPC** – Tokens per correct
- **$100C** – Estimated cost per 100 correct answers
- **Notes** – Quick observations (format issues, SR dominates, GEPA win, accuracy saturated, etc.)

---

## Checklist per Dataset
For each dataset:
- [ ] Run `setup_data.py` with correct split sizes
- [ ] Run Baseline → record results
- [ ] Run Self-Refine → record results
- [ ] Run GEPA → record results
- [ ] Note any anomalies (format violations, unusually high/low token use)