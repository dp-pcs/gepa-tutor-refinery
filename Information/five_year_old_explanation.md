The super simple version
	•	We have quizzes (datasets).
Each quiz has:
	•	a question
	•	a few choices (A, B, C…)
	•	the answer key (the correct letter)
	•	Our program makes the model pick a letter.
We then check its last line: Answer: <LETTER>.
If that letter matches the answer key, it’s right. If not (or format is wrong), it’s wrong.
Your pass rate = how many it got right.
	•	Three ways we ask the model to answer:
	1.	Baseline: one shot. “Here’s the question & choices → give the letter.”
	2.	Self‑Refine: two shots.
	•	Shot 1: try an answer.
	•	Shot 2: read its own first try, fix mistakes, then give the final Answer: <LETTER>.
(This often helps, but costs two calls.)
	3.	GEPA: learn a better instruction sheet (prompt) before answering.
	•	Look at mistakes on a small set.
	•	Write prompt edits (Variants A/B/C).
	•	Test those edits.
	•	Keep the best one and use it as the new single‑call prompt.
	•	Distill from Self‑Refine: Self‑Refine is the teacher that shows how to fix answers. We boil down (distill) those fixes into a one‑call prompt so we don’t pay for two calls every time.

That’s it. Quizzes, answer key, three ways to answer, and one “teacher → rulebook” move.

What the prompt lines m ean (plain English)
	•	“Restate the question, quote one sentence, eliminate wrong options, then final letter”
= we give the model a mini playbook so it thinks in small steps.
	•	“Ensure answer choices align with the question stem”
= make sure you’re answering what is asked (e.g., if the question says “Which is NOT true?”, don’t pick a true statement).
	•	“Clarify the question stem”
= rewrite the ask in your own short words so you don’t miss tricks like EXCEPT, least, most, false, could be true, etc.
	•	“Provide a clear rationale”
= one short reason why your letter wins. (We still only grade the final Answer: <LETTER>.)
	•	The line you saw in a GEPA variant: “Identify the flaw in the argument…”
= that’s LSAT‑LR style. It’s fine for argument‑based sets, but on science/math datasets it can confuse the model. Keep dataset‑specific lines in dataset‑specific prompts.