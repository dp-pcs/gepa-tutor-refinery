20‑minute plan to get back on track

Step 1 — Replace the “answer‑only” distilled prompt with a minimal‑scaffold distilled prompt

Keep the final answer line requirement but allow exactly two short lines before it. This usually unlocks big accuracy.

New distilled prompt candidate (drop‑in as a variant):

You are an exam solver for multiple‑choice questions with 5–10 options.

Before the final answer:
- Write ONE short elimination line that names 2–3 clearly wrong options (≤15 words).
- Write ONE short tie‑breaker line comparing the last two candidates (≤15 words).
Then output exactly one final line: Answer: <LETTER>

FORMAT (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER must be one of the letters shown in CHOICES (e.g., A–J).
- Do NOT add any text after the final answer line.

Why this helps:
	•	Gives the model a tiny scaffold (2 lines) to decide among many options.
	•	Still easy to grade: we only parse the final Answer: line; extra lines are allowed.

Step 2 — Evaluate that prompt as a single call

Two quick options:

# Option A (quick): overwrite the runtime prompt
cp runs/.../variant_new/prompt.txt src/base_tutor_prompt.txt
python -m src.run_loop --config configs/config.yaml --mode baseline

Check summary.json and dev/test/records.jsonl.

Step 3 — If accuracy is still low, add 2–3 few‑shot mini examples

Add two tiny few‑shots inside the distilled prompt (before instructions). Keep them uniform:

Example:
Q: [short question]
Choices: A)... B)... C)... D)... E)...
Eliminate: B (contradiction); D (definition mismatch)
Tie-break: A vs C → A matches condition precisely
Answer: A
Two examples (one logic, one math-ish) can lift 10‑choice accuracy a lot. Keep them short; your parser still keys off the last Answer: line in the real question.

Step 4 — Re‑run GEPA with a gentle efficiency constraint

Once the minimal‑scaffold prompt is decent, let GEPA propose 3–4 edits but cap verbosity:

Add to the reflection template:

Constraints: Keep any added rules ≤3 lines total. Do not increase output length beyond 2 short lines + final answer.

This prevents variants from inflating tokens.

Quick diagnostics to be sure we’re measuring the right thing

Run these on the test split of your distilled run:
	1.	Predicted letter spread

 jq -r '.answer_pred' runs/.../test/records.jsonl | sort | uniq -c


If it’s all one letter (e.g., always “C”), the prompt is too generic; the few‑shot and the tie‑breaker line fix this.
	2.	Gold letter spread

    jq -r '.answer_gold' runs/.../test/records.jsonl | sort | uniq -c

    We want a mix A–J; if not, something’s off in the loader.
	3.	Compliance rate

    jq -r 'select(.answer_pred==null)' runs/.../test/records.jsonl | wc -l

    Should be 0 with your strict prompts. If not, a formatting slip remains.


