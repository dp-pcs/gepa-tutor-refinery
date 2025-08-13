let's documen t and try a hybrid SR to GEPA prompt chain

Step 1 – Self-Refine (SR) Prompt
You are a **reading and science tutor**.
For each multiple-choice question:
1) Restate the question briefly.
2) Quote exactly **one** evidence sentence from the passage (if provided).
3) Eliminate wrong options with a one-line reason each.
4) Choose the best answer **by letter only** (A/B/C/D) on a final line: `Answer: <LETTER>`.
5) Keep explanations concise (<= 120 tokens).

Identify the flaw in the argument by pinpointing the unsupported assumption or logical error.

FORMATTING RULES (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER is one of A-J only (depending on number of choices).
- Do NOT put any other letters on that line.
- Do NOT add text after the final answer line.

Step 2 – GEPA Pass (Variant B style)

Take only the SR output (don’t re-feed the original question) and run:
You are reviewing an answer from a reading and science tutor for a multiple-choice question.

Task:
1) Ensure the evidence sentence directly supports the main argument without ambiguity.
2) If the chosen answer is supported, restate the reasoning clearly in <= 60 tokens.
3) If the chosen answer is unsupported or flawed, correct it and provide a better-supported choice.
4) End with a final line: Answer: <LETTER>

FORMATTING RULES:
- Final line MUST be exactly: Answer: <LETTER>
- Keep the explanation concise and logically sound.
- Do NOT include multiple answer letters anywhere in the output.


⸻

How to Implement
	•	Pipeline: Dataset → SR Prompt → SR Output → GEPA Prompt → Final Answer
	•	Eval: Compare final answers from hybrid to SR-only answers.
	•	Goal: Beat SR’s ~0.4% LSAT_LR test accuracy with minimal extra token cost.

⸻

Why This Might Work
	•	SR is great at breaking the problem down.
	•	GEPA acts as a “logic & evidence auditor” to catch subtle reasoning mistakes without redoing the whole solve.
	•	Smaller second pass = lower token overhead than running GEPA from scratch.



Here’s a minimal Python wrapper you can drop into your existing eval pipeline to run the SR → GEPA hybrid without messing with your main loop.

This assumes:
	•	You already have code that runs a prompt against your LLM and gets a string back (run_llm(prompt) in my example).
	•	You can swap in your own dataset loader and scoring function.

    import json

# -------------------
# HYBRID SR → GEPA WRAPPER
# -------------------

def run_llm(prompt):
    """
    Replace this with your existing LLM call.
    Should take a string prompt and return the model's raw string output.
    """
    raise NotImplementedError

def sr_prompt(question, passage):
    return f"""You are a **reading and science tutor**.
For each multiple-choice question:
1) Restate the question briefly.
2) Quote exactly **one** evidence sentence from the passage (if provided).
3) Eliminate wrong options with a one-line reason each.
4) Choose the best answer **by letter only** (A/B/C/D) on a final line: `Answer: <LETTER>`.
5) Keep explanations concise (<= 120 tokens).

Identify the flaw in the argument by pinpointing the unsupported assumption or logical error.

FORMATTING RULES (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER is one of A-J only (depending on number of choices).
- Do NOT put any other letters on that line.
- Do NOT add text after the final answer line.

Question:
{question}

Passage:
{passage}
"""

def gepa_review_prompt(sr_output):
    return f"""You are reviewing an answer from a reading and science tutor for a multiple-choice question.

Task:
1) Ensure the evidence sentence directly supports the main argument without ambiguity.
2) If the chosen answer is supported, restate the reasoning clearly in <= 60 tokens.
3) If the chosen answer is unsupported or flawed, correct it and provide a better-supported choice.
4) End with a final line: Answer: <LETTER>

FORMATTING RULES:
- Final line MUST be exactly: Answer: <LETTER>
- Keep the explanation concise and logically sound.
- Do NOT include multiple answer letters anywhere in the output.

Here is the tutor's answer to review:
{sr_output}
"""

def run_hybrid(question, passage):
    # Step 1 – SR pass
    sr_out = run_llm(sr_prompt(question, passage))
    
    # Step 2 – GEPA review pass
    gepa_out = run_llm(gepa_review_prompt(sr_out))
    
    return gepa_out

# -------------------
# Example usage
# -------------------
if __name__ == "__main__":
    # Example single question
    q = "Which choice best describes the main flaw in the author's reasoning?"
    p = "The author assumes that because the event happened after the law was passed, the law caused the event."

    final_answer = run_hybrid(q, p)
    print("Final Hybrid Output:\n", final_answer)

    How to Integrate into Your Eval
	1.	Hook into your existing dataset loop where you normally call SR or GEPA directly.
	2.	Instead of calling one prompt, call run_hybrid(question, passage).
	3.	The returned string will be in the correct Answer: <LETTER> format for your scoring function.
	4.	Measure accuracy, tokens used, and compare against SR-only.