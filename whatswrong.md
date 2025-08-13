What’s wrong (and why it hurts)
	1.	Letter‑set mismatch.
In step 4 you say “(A/B/C/D)”, then later the formatting rules allow A–J. On 10‑choice questions, that contradiction nudges the model toward A–D only, which can’t possibly be right when the gold is, say, H. That alone can explain the 20% ceiling.
	2.	Task mismatch language.
The header says “reading and science tutor” and the distilled rule references a passage. MMLU‑Pro has no passage. This primes the model to look for evidence that isn’t there, wasting tokens and sometimes derailing the format.
	3.	Garbage bytes at EOF.
I see non‑printable characters at the end: …passage.%…. These can corrupt the prompt the model receives.
	4.	Rules too generic.
“Ensure justification aligns with the passage” is vague and not diagnostic for logic/math/facts; it doesn’t teach the model how to choose among 10 options.

⸻

Quick fixes (copy/paste)

A) Use a no‑passage MCQ distilled prompt

Drop this in as a new candidate (e.g., variant_D/prompt.txt) and test:
You are an exam solver for multiple‑choice questions.

For each question:
1) Do NOT restate the question.
2) Eliminate clearly wrong options with at most one short reason each (≤1 line total).
3) If two options are plausible, compare them on one decisive criterion and pick the better.
4) Output only one final line: Answer: <LETTER>

FORMATTING RULES (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER must be one of the letters shown in CHOICES (e.g., A–J).
- Do NOT add any text after the final answer line.
- Violating these rules counts as incorrect.

B) Make the allowed letters dynamic

Patch render_mcq_prompt in src/evaluator.py so the prompt tells the model the exact letter set:

def render_mcq_prompt(base_prompt: str, ex: Example) -> str:
    choices_text = "\n".join([f"{c['label']}. {c['text']}" for c in ex.choices])
    letters = "/".join([c['label'] for c in ex.choices])  # e.g., A/B/C/.../J
    ctx = f"PASSAGE: {ex.context}\n" if ex.context else ""
    return f"""{base_prompt}

{ctx}QUESTION: {ex.question}
CHOICES:
{choices_text}

Allowed answer letters: {letters}
End with exactly one line: Answer: <LETTER>"""

Also update your base/distilled prompts to remove “(A/B/C/D)” and instead say “one of the letters shown in CHOICES.”

C) Strip non‑printable bytes from prompts

On macOS:

LC_ALL=C tr -cd '\11\12\15\40-\176' < runs/.../variant_A/prompt.txt > /tmp/clean.txt \
  && mv /tmp/clean.txt runs/.../variant_A/prompt.txt

  Or just open the file and delete trailing junk.
How to evaluate the distilled prompt as a single‑call (no training cost)

Right now your distilled variants live under training/. To test inference‑time cost/accuracy:

Option 1 (quick): overwrite the runtime prompt and run baseline:

cp runs/20250812-145922_distill_from_self_refine/training/variant_D/prompt.txt src/base_tutor_prompt.txt
python src/run_loop.py --config configs/config.yaml --mode baseline

Option 2 (cleaner): add a CLI flag to load a prompt file (I can give you a tiny patch if you want). Either way, this must be one call per question.

⸻

What “good” should look like after fixes

On the same MMLU‑Pro slice:
	•	Self‑Refine (2 calls): still ~100% accuracy, ~500–550 tokens/question.
	•	Distilled (1 call, fixed prompt): much higher than 20%—ideally within a few points of SR if distillation is working; costs ~100–180 tokens/question.
	•	GEPA variants: now obey formatting; some may climb above 20–40% while staying ~100–140 tokens.

If the distilled prompt is still weak, run another distill round with stronger guidance:

Distill reflection prompt (swap into your distill mode):
You will see CORRECT Self‑Refine traces (question, choices, final letter).
Induce 3–4 concise rules (≤3 lines each) that explain why those revisions worked on 10‑choice MCQ across logic/math/knowledge tasks.
Rules must:
- NOT restate the question
- Use 1–2 eliminations total (brief)
- Include a tie‑breaker comparison step for the final two candidates
- Preserve the final line format exactly

Return JSON: { "rules": [...], "edits": [{"name":"A","text":"<3–5 lines>","why":"<what it enforces>"}] }
Guardrails for fair comparisons
	•	Strict parser only counts Answer: <LETTER> (you already did).
	•	Two‑call totals for SR (input+output tokens, combined latency).
	•	Include tokens per correct and cost per 100 correct in the report.
	•	Keep choice shuffling on (you already added it).

⸻

What to do next (short checklist)
	1.	Apply the letter‑set fix and no‑passage distilled prompt.
	2.	Clean the non‑printable bytes.
	3.	Re‑evaluate distilled as baseline (one call).
	4.	Re‑run GEPA (it should now respect the format and letter set).
	5.	Send me the updated summary.csv rows and the new variants.json pareto section.

If the distilled prompt lands within ~2–5 points of SR at ~¼–⅓ the tokens, that’s the headline: “Self‑Refine accuracy, single‑call cost.” If it’s still far off, we’ll iterate the distill reflections using more SR‑correct traces and a stricter “no restating, tie‑break once” rule.