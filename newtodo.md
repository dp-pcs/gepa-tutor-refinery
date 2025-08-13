2) How to judge “better” (Pareto, not vibes)

A method is strictly better only if it dominates on the two axes that matter to you:
	•	Accuracy (↑) on held‑out test, and
	•	Total cost (↓) (tokens + latency, summing all calls at inference).

If Self‑Refine hits 100% and uses less total cost per question than your GEPA prompt, it dominates. In that case, use Self‑Refine—or use GEPA to reverse‑engineer a static prompt that matches Self‑Refine’s behavior without the second call.

Key fairness rule: for Self‑Refine you must count both calls’ input+output tokens and combined latency. Otherwise it will look cheaper than it is.

⸻

3) Why your current numbers raise flags

“Self‑Refine is 100%… GEPA goes from 20→40% but more tokens. Why is GEPA better?”

Short answer: it isn’t better on those numbers. Your read is right. Two likely issues are distorting the comparison:

(a) Token accounting (very likely)

Your current evaluator logs only the second call’s output tokens in Self‑Refine. That undercounts by a lot.

Fix (minimal change) — in src/evaluator.py, when strategy == "self_refine":
	•	Keep the first call’s usage and add it to the second call’s usage.
	•	Compute and store total_input_tokens, total_output_tokens, total_tokens_all_calls, and sum latency across both calls.

Then use total_tokens_all_calls for comparisons and for Pareto.

(b) 100% on a 10‑choice (A–J) MMLU‑Pro slice is unusual

It’s not impossible on small slices, but it’s rare. Triple‑check:
	•	Parsing strictness: Require only Answer: <LETTER> (A–J). Remove the fallback that grabs the last capital letter anywhere in text.
	•	Choice shuffling: You added it—good. Make sure gold remapping is correct after the shuffle.
	•	Provider sanity: Confirm Self‑Refine is really using the OpenAI provider and not your “Always‑A” or mock for either call.

If after those fixes Self‑Refine is still 100% on large test sets (e.g., 200), great—that means it truly dominates. Your article should say that, and then either (i) show GEPA efficiency gains on a saturated task or (ii) switch to a task where GEPA can improve accuracy.

⸻

Concrete patches (tiny and targeted)

A) Fair tokens for Self‑Refine

In src/evaluator.py, replace the Self‑Refine block with:

elif strategy == "self_refine":
    # 1) initial
    r1 = provider.generate(prompt)

    # 2) critique + revise with full context
    choices_text = "\n".join([f"{c['label']}. {c['text']}" for c in ex.choices])
    crit = f"""You will critique and revise an answer to a multiple-choice question.

PASSAGE:
{ex.context or "(no passage)"}

QUESTION:
{ex.question}

CHOICES:
{choices_text}

INITIAL ANSWER:
{r1.text}

Instructions:
- If the initial answer is already correct and justified, you may keep it.
- Otherwise, briefly state the likely mistake (one short line).
- Then output a corrected final line strictly as: Answer: <LETTER>
Only output at most two short lines and always include the final 'Answer: <LETTER>' line."""
    r2 = provider.generate(crit)

    # Parse final
    result = r2
    answer = parse_answer_letter(result.text)
    if answer is None:
        answer = parse_answer_letter(r1.text)

    # --- NEW: fair token & latency accounting ---
    def _tok(u): 
        if isinstance(u, dict):
            return (u.get("input_tokens") or 0, u.get("output_tokens") or 0)
        return (0, 0)

    in1, out1 = _tok(r1.usage); in2, out2 = _tok(r2.usage)
    total_in = in1 + in2
    total_out = out1 + out2
    total_tokens_all_calls = total_in + total_out
    total_latency = r1.latency_sec + r2.latency_sec

    When you append the rows.append({...}), add these fields:

    "usage": {
  "call1": r1.usage, "call2": r2.usage,
  "total_input_tokens": total_in,
  "total_output_tokens": total_out,
  "total_tokens_all_calls": total_tokens_all_calls,
},
"latency_sec": total_latency,
And when you compute averages at the end, use total_tokens_all_calls instead of output-only tokens for Self‑Refine.

(For baseline/GEPA single‑call, just map the single call into the same fields so summaries stay consistent.)

B) Strict answer parsing (avoid false positives)

In src/utils.py, tighten parse_answer_letter:
def parse_answer_letter(text: str) -> str | None:
    # Strict: require explicit 'Answer: <LETTER>' with A–J support
    m = re.search(r"(?im)^\\s*Answer\\s*:\\s*([A-J])\\b", text)
    return m.group(1).upper() if m else None
    No fallback to “last capital letter.” If the model doesn’t follow the format, it gets scored wrong. That’s fair and stabilizes evals.

⸻

Reading your current results (with the right lens)
	•	If, after fixes, Self‑Refine = 100% and cheaper (true total tokens) → it dominates. Ship Self‑Refine for that task. GEPA can still be used to try to “bake in” similar behavior into one call, but if it can’t match the accuracy/cost, show that honestly.
	•	If GEPA improves baseline accuracy but costs more tokens than Self‑Refine → it’s a partial win. Note the trade‑off; consider running efficiency‑mode GEPA to push variants toward shorter outputs (you already have that patch path), or reduce edit verbosity in the reflection prompt (e.g., “cap new rules to ≤3 lines; avoid restating the question; forbid extra prose”).
	•	Remember the point: GEPA is valuable because it produces a deployable prompt. When Self‑Refine is best on accuracy and cheaper after fair accounting, you choose Self‑Refine. When accuracy is saturated, GEPA often gives efficiency wins; when accuracy isn’t saturated, GEPA can give accuracy wins with one call.

⸻

What I’d do next (in order)
	1.	Apply the two patches (fair tokens; strict parsing).
	2.	Re‑run the same MMLU‑Pro slice with OpenAI:
	•	baseline → self_refine → gepa → report.
	3.	Post the new report/summary.csv and (from GEPA) round1/variants.json’s pareto list.
	4.	Decision:
	•	If Self‑Refine still dominates → that’s your headline for this dataset.
	•	If GEPA closes the gap or wins on cost for ≈same accuracy → showcase that as the “baked‑in, one‑call” variant.