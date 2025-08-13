I explored the `gepa-tutor-refinery` repository and found that the pipeline uses a **base tutor prompt**, a **self‑refine step**, and a **GEPA‐style reflective prompt evolution**.  The key pieces are:

* **`src/evaluator.py`** – builds the prompt from the question and choices, runs the LLM via a provider, parses the final `Answer:` line and counts tokens.  It supports baseline, self‑refine (two‑call), GEPA and hybrid modes.  In self‑refine, the first call answers the question and the second call critiques and revises; the code combines the token usage for both calls.  If the second call doesn’t produce a valid `Answer: <LETTER>`, it falls back to the first answer.

* **`src/reflect_and_edit.py`** – defines a reflection prompt asking the LLM to look at **failed examples** and propose up to three **prompt edits**.  Each edit must be *self‑contained*, no more than five lines, and must preserve the final line format of `Answer: <LETTER>`.  The `reflect()` function collects the failed rows, compiles them into a JSON snippet, appends the base prompt, asks the LLM to produce rules and edits, and returns the parsed JSON.  The edits are then appended to the base prompt to create variants.

* **`src/run_loop.py`** – orchestrates training runs.  In GEPA mode it evaluates the base prompt on the dev set, identifies failed examples, calls `reflect()` to obtain edits, constructs prompt variants (A, B, C), evaluates them on the dev set and uses a Pareto filter (accuracy vs. tokens) to pick the best variant.  This chosen prompt is evaluated on the test set and saved under `runs/<timestamp>_gepa/…`.

From reviewing the code and your test results, a few points help explain why **more refinements can harm performance**:

1. **Task mismatch & over‑complex prompts** – the base tutor prompt and many GEPA edits assume every question has a “passage” and needs evidence sentences.  Datasets like TruthfulQA‑MC and some LSAT tasks have no passage; quoting nonexistent evidence confuses the model and wastes tokens.

2. **Strict format requirements** – your evaluator requires the **final line** to be exactly `Answer: <LETTER>`.  If a variant or GEPA edit adds extra text after the answer or breaks the format, every such response is marked wrong.  Several GEPA variants add reasoning after the answer, causing 0 % accuracy on test.

3. **Token explosion with little accuracy gain** – self‑refine uses two full calls per question.  Unless the second call significantly improves accuracy, the cost per correct answer can balloon.  GEPA variants that add long justification steps also increase tokens without necessarily improving accuracy.

4. **Overfitting to the dev split** – the reflection step uses only a small dev set to generate edits.  An edit that helps on a handful of dev examples may not generalize to harder test questions; this is why some GEPA variants perform worse than the base prompt on the test set.

5. **Hybrid approach complexity** – the hybrid (SR → GEPA) runs the model twice and tries to audit its own reasoning.  In practice it inherits the mistakes of the first call and multiplies token cost, and if the prompts are mis‑aligned with the dataset (e.g., quoting evidence on a question with no passage) the hybrid can perform worse than self‑refine alone.

### Recommendations

* **Simplify and adapt prompts per dataset** – drop passage‑quoting steps when no passage is provided; avoid adding LSAT‑style logic‑flaw instructions to science questions.  This reduces format violations and token waste.

* **Use shorter, more targeted edits** – GEPA edits that force the model to stay concise (e.g., limit the number of elimination lines or forbid restating the question) can reduce tokens without harming accuracy.

* **Hold out a larger dev set** – using more diverse failed examples in the reflection step can help the LLM learn more generalizable edits.

* **Compare cost per correct** – instead of looking only at raw accuracy, consider tokens per correct answer or cost per correct.  A variant that slightly lowers accuracy but halves the token cost may still be preferred.

* **Don’t over‑refine** – once a variant no longer improves accuracy on a validation set, stop adding rules; each extra rule adds complexity and risk of misinterpretation.

By focusing on dataset‑appropriate prompts, carefully managing the length and content of GEPA edits, and evaluating efficiency as well as accuracy, you can keep the benefits of prompt refinement without incurring worse results.
