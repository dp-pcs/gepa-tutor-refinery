import time, pathlib, json, statistics, re
from dataclasses import dataclass
from typing import List, Dict, Any
from .models.provider import Provider
from .utils import ensure_dir, write_jsonl, parse_answer_letter


@dataclass
class Example:
    id: str
    context: str
    question: str
    choices: list[dict]
    answer: str


@dataclass
class EvalResult:
    accuracy: float
    avg_tokens_out: float | None
    avg_latency_sec: float
    records_path: str


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


def run_eval(provider: Provider, base_prompt: str, examples: List[Example], strategy: str = "baseline", self_refine_steps: int = 1, out_dir: str = "runs/tmp") -> EvalResult:
    ensure_dir(out_dir)
    rows = []
    correct = 0
    tokens_list, latency_list = [], []
    
    for ex in examples:
        # Choice shuffling for robustness (prevents label memorization)
        import random
        rng = random.Random(12345 + hash(ex.id) % 10_000_000)
        
        perm = list(range(len(ex.choices)))
        rng.shuffle(perm)
        shuffled_choices = [ex.choices[i] for i in perm]
        
        # map gold to its new position
        label_to_idx = {c['label']: idx for idx, c in enumerate(ex.choices)}
        gold_idx = label_to_idx[ex.answer]
        new_gold_idx = perm.index(gold_idx)
        new_gold_letter = chr(ord('A') + new_gold_idx)
        
        # verify the mapping is correct
        assert ex.choices[gold_idx]["text"] == shuffled_choices[new_gold_idx]["text"], f"Choice mapping error: {ex.choices[gold_idx]['text']} != {shuffled_choices[new_gold_idx]['text']}"
        
        # create shuffled example for this run
        ex_for_run = Example(ex.id, ex.context, ex.question,
                             [{"label": chr(ord('A')+i), "text": c["text"]} for i, c in enumerate(shuffled_choices)],
                             new_gold_letter)
        

        
        # Initialize with generic prompt, will be overridden for hybrid mode
        prompt = render_mcq_prompt(base_prompt, ex_for_run)
        rendered = prompt
        
        if strategy == "baseline":
            result = provider.generate(prompt)
            answer = parse_answer_letter(result.text)
            
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
            result = r2
            answer = parse_answer_letter(result.text)

            # Guardrail: if revision didn't yield a letter, fall back to initial
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
                
        elif strategy == "distill_from_self_refine":
            # Use Self-Refine's correct traces to distill into a single-call prompt
            # This is a special mode that runs Self-Refine first, then distills the behavior
            
            # 1) Run Self-Refine to get correct traces
            r1 = provider.generate(prompt)
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
            
            # 2) Distill the behavior into rules
            distill_prompt = f"""Analyze this Self-Refine correction and extract the implicit rules:

INITIAL ANSWER: {r1.text}
CORRECTED ANSWER: {r2.text}
QUESTION: {ex.question}
CHOICES: {choices_text}

What rules did the model implicitly follow to fix the error? Make 3-5 concise, enforceable edits (≤3 lines each) that could be appended to the base prompt.

Focus on:
- Error detection patterns
- Correction strategies  
- Format enforcement
- Reasoning improvements

Output only the rules, one per line, starting with "- "."""
            
            distill_result = provider.generate(distill_prompt)
            
            # 3) Use the distilled prompt for the final answer
            enhanced_prompt = prompt + "\n\nDISTILLED RULES:\n" + distill_result.text
            result = provider.generate(enhanced_prompt)
            answer = parse_answer_letter(result.text)
            
            # Fallback to Self-Refine if distillation fails
            if answer is None:
                answer = parse_answer_letter(r2.text)
                result = r2
            
            # Token accounting: count distillation + final call
            def _tok(u): 
                if isinstance(u, dict):
                    return (u.get("input_tokens") or 0, u.get("output_tokens") or 0)
                return (0, 0)
            
            # Count all calls: initial + critique + distillation + final
            in1, out1 = _tok(r1.usage)
            in2, out2 = _tok(r2.usage) 
            in3, out3 = _tok(distill_result.usage)
            in4, out4 = _tok(result.usage)
            
            total_in = in1 + in2 + in3 + in4
            total_out = out1 + out2 + out3 + out4
            total_tokens_all_calls = total_in + total_out
            total_latency = r1.latency_sec + r2.latency_sec + distill_result.latency_sec + result.latency_sec
                
        elif strategy == "hybrid":
            # Hybrid: SR → GEPA Review (2-stage chain)
            
            # Token counting helper for hybrid
            def _tok(u, key, default=0):
                if isinstance(u, dict):
                    return u.get(key, default)
                return default
            
            # Build choices text for hybrid prompts
            choices_text = "\n".join([f"{c['label']}. {c['text']}" for c in ex_for_run.choices])
            letters = ", ".join([c['label'] for c in ex_for_run.choices])
            
            # Dataset-specific prompt tailoring
            dataset_name = ex.id.split(':')[0] if ':' in ex.id else "unknown"
            
            if dataset_name == "truthfulqa":
                # TruthfulQA: Focus on fact-checking and adversarial trap detection
                sr_prompt = f"""You are a **fact-checking tutor** specializing in detecting misleading claims.

For each multiple-choice question:
1) Restate the question briefly.
2) Identify the main claim being tested.
3) Eliminate wrong options by detecting:
   - Unsupported assumptions
   - Logical fallacies
   - Factual inaccuracies
   - Adversarial traps
4) Choose the most factually accurate answer **by letter only** on a final line: `Answer: <LETTER>`
5) Keep explanations concise (<= 120 tokens).

FORMATTING RULES (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER is one of {letters} only.
- Do NOT put any other letters on that line.
- Do NOT add text after the final answer line.

FORMAT EXAMPLES:
✅ CORRECT: "Answer: A"
✅ CORRECT: "The answer is clearly A. Answer: A"
❌ WRONG: "Answer: A and B"
❌ WRONG: "I think the answer is A"
❌ WRONG: "Answer: A because..."

Question:
{ex.question}

CHOICES:
{choices_text}

Allowed answer letters: {letters}
End with exactly one line: Answer: <LETTER>"""
                # Update rendered for logging
                rendered = sr_prompt
                
                gepa_review_prompt = f"""You are a **fact-checking auditor** reviewing an answer for accuracy.

Task:
1) Verify the chosen answer is factually correct and well-supported.
2) If the answer is correct, confirm in <= 40 tokens.
3) If the answer is wrong, identify the correct choice with brief reasoning.
4) End with exactly: Answer: <LETTER>

FORMATTING RULES:
- Final line MUST be exactly: Answer: <LETTER>
- Keep explanation concise and factual.
- Be confident and decisive in your review.

FORMAT EXAMPLES:
✅ CORRECT: "Answer: A"
✅ CORRECT: "The answer is correct. Answer: A"
❌ WRONG: "Answer: A and B"
❌ WRONG: "I think Answer: A"

Here is the tutor's answer to review:
{{SR_OUTPUT}}

Original Question:
{ex.question}

CHOICES:
{choices_text}

Allowed answer letters: {letters}"""

            elif dataset_name == "lsat_lr":
                # LSAT-LR: Focus on logical reasoning and flaw detection
                sr_prompt = f"""You are a **logical reasoning tutor** specializing in argument analysis.

For each multiple-choice question:
1) Restate the question briefly.
2) Identify the main argument and its conclusion.
3) Eliminate wrong options by detecting:
   - Logical flaws
   - Unsupported assumptions
   - Reasoning gaps
   - Irrelevant information
4) Choose the most logically sound answer **by letter only** on a final line: `Answer: <LETTER>`
5) Keep explanations concise (<= 120 tokens).

FORMATTING RULES (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER is one of {letters} only.
- Do NOT put any other letters on that line.
- Do NOT add text after the final answer line.

FORMAT EXAMPLES:
✅ CORRECT: "Answer: B"
✅ CORRECT: "The logical flaw is clear. Answer: B"
❌ WRONG: "Answer: B and C"
❌ WRONG: "I believe the answer is B"
❌ WRONG: "Answer: B because..."

Question:
{ex.question}

CHOICES:
{choices_text}

Allowed answer letters: {letters}
End with exactly one line: Answer: <LETTER>"""
                # Update rendered for logging
                rendered = sr_prompt
                
                gepa_review_prompt = f"""You are a **logical reasoning auditor** reviewing an answer for soundness.

Task:
1) Verify the chosen answer follows logically from the reasoning.
2) If the logic is sound, confirm in <= 40 tokens.
3) If there's a logical flaw, identify the correct choice with brief reasoning.
4) End with exactly: Answer: <LETTER>

FORMATTING RULES:
- Final line MUST be exactly: Answer: <LETTER>
- Keep explanation focused on logical soundness.
- Be confident and decisive in your review.

FORMAT EXAMPLES:
✅ CORRECT: "Answer: B"
✅ CORRECT: "The logic is sound. Answer: B"
❌ WRONG: "Answer: B and C"
❌ WRONG: "I believe Answer: B"

Here is the tutor's answer to review:
{{SR_OUTPUT}}

Original Question:
{ex.question}

CHOICES:
{choices_text}

Allowed answer letters: {letters}"""

            else:
                # Generic: Adapt based on whether passage exists
                if ex.context and ex.context.strip() and ex.context != "No passage provided":
                    # With passage: Use evidence-based reasoning
                    sr_prompt = f"""You are a **reading and science tutor**.

For each multiple-choice question:
1) Restate the question briefly.
2) Quote exactly **one** evidence sentence from the passage.
3) Eliminate wrong options with a one-line reason each.
4) Choose the best answer **by letter only** on a final line: `Answer: <LETTER>`
5) Keep explanations concise (<= 120 tokens).

FORMATTING RULES (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER is one of {letters} only.
- Do NOT put any other letters on that line.
- Do NOT add text after the final answer line.

Question:
{ex.question}

Passage:
{ex.context}

CHOICES:
{choices_text}

Allowed answer letters: {letters}
End with exactly one line: Answer: <LETTER>"""
                else:
                    # Without passage: Use logical reasoning
                    sr_prompt = f"""You are a **logical reasoning tutor**.

For each multiple-choice question:
1) Restate the question briefly.
2) Use logical reasoning to analyze the options.
3) Eliminate wrong options with a one-line reason each.
4) Choose the best answer **by letter only** on a final line: `Answer: <LETTER>`
5) Keep explanations concise (<= 120 tokens).

FORMATTING RULES (CRITICAL):
- Final line MUST be exactly: Answer: <LETTER>
- LETTER is one of {letters} only.
- Do NOT put any other letters on that line.
- Do NOT add text after the final answer line.

Question:
{ex.question}

CHOICES:
{choices_text}

Allowed answer letters: {letters}
End with exactly one line: Answer: <LETTER>"""
                
                # Update rendered for logging
                rendered = sr_prompt
                
                # Generic GEPA review
                gepa_review_prompt = f"""You are reviewing an answer from a tutor for a multiple-choice question.

Task:
1) Verify the chosen answer is well-reasoned and correct.
2) If the answer is correct, confirm in <= 40 tokens.
3) If the answer is wrong, identify the correct choice with brief reasoning.
4) End with exactly: Answer: <LETTER>

FORMATTING RULES:
- Final line MUST be exactly: Answer: <LETTER>
- Keep explanation concise and focused.

Here is the tutor's answer to review:
{{SR_OUTPUT}}

Original Question:
{ex.question}

CHOICES:
{choices_text}

Allowed answer letters: {letters}"""

            sr_result = provider.generate(sr_prompt)
            sr_tokens = _tok(sr_result.usage, "input_tokens", 0) + _tok(sr_result.usage, "output_tokens", 0)
            
            # Format GEPA review prompt with actual SR output
            gepa_review_prompt_formatted = gepa_review_prompt.replace("{{SR_OUTPUT}}", sr_result.text)
            
            # Stage 2: GEPA reviews SR's output and acts as logic auditor
            gepa_result = provider.generate(gepa_review_prompt_formatted)
            gepa_tokens = _tok(gepa_result.usage, "input_tokens", 0) + _tok(gepa_result.usage, "output_tokens", 0)
            
            # Format lock: Auto-correct GEPA output parsing violations
            sr_answer = parse_answer_letter(sr_result.text)
            gepa_answer = parse_answer_letter(gepa_result.text)
            
                        # Enhanced error recovery with intelligent confidence scoring
            def calculate_gepa_confidence(gepa_output, sr_output, sr_answer, gepa_answer):
                """Calculate confidence score for GEPA override decision"""
                confidence = 0.0

                # Base confidence from output quality
                if len(gepa_output.strip()) <= 50:  # Very concise
                    confidence += 0.2
                elif len(gepa_output.strip()) <= 100:  # Moderately concise
                    confidence += 0.15

                # Check if GEPA made a clear correction with reasoning
                if "correct" in gepa_output.lower() or "wrong" in gepa_output.lower():
                    confidence += 0.25

                # Check if GEPA provided logical reasoning
                if any(word in gepa_output.lower() for word in ["because", "since", "as", "due to", "reason", "logic"]):
                    confidence += 0.2

                # Check if GEPA is very confident (strong language)
                if any(word in gepa_output.lower() for word in ["clearly", "obviously", "definitely", "certainly", "must", "should"]):
                    confidence += 0.15

                # Check if GEPA identified a specific flaw in SR's reasoning
                if any(word in gepa_output.lower() for word in ["flaw", "error", "mistake", "incorrect", "wrong"]):
                    confidence += 0.25

                # Bonus for very specific corrections
                if "the answer is" in gepa_output.lower() and gepa_answer != sr_answer:
                    confidence += 0.1

                # PHASE 3.4: Additional confidence factors based on analysis
                # Check for strong disagreement language
                if any(word in gepa_output.lower() for word in ["incorrect", "wrong", "mistake", "error"]):
                    confidence += 0.15
                
                # Check for specific answer correction
                if gepa_answer and sr_answer and gepa_answer != sr_answer:
                    confidence += 0.1
                
                # Check for clear reasoning structure
                if any(word in gepa_output.lower() for word in ["therefore", "thus", "hence", "consequently"]):
                    confidence += 0.1

                return min(confidence, 1.0)
            
            # Calculate confidence for GEPA override
            gepa_confidence = calculate_gepa_confidence(gepa_result.text, sr_result.text, sr_answer, gepa_answer)
            
            if gepa_answer is not None and gepa_answer != sr_answer:
                # GEPA made a change - use it if it's valid AND confident enough
                if any(gepa_answer == c['label'] for c in ex_for_run.choices):
                    if gepa_confidence >= 0.5:  # PHASE 3.4: Optimized threshold for better override success
                        result = gepa_result
                        answer = gepa_answer
                        print(f"GEPA override (conf: {gepa_confidence:.2f}): {sr_answer} → {gepa_answer} for {ex.id}")
                    else:
                        # Low confidence - stick with SR
                        result = sr_result
                        answer = sr_answer
                        print(f"GEPA low confidence ({gepa_confidence:.2f}), using SR: {sr_answer} for {ex.id}")
                else:
                    # GEPA's answer is invalid, fall back to SR
                    result = sr_result
                    answer = sr_answer
                    print(f"GEPA invalid answer '{gepa_answer}', using SR: {sr_answer} for {ex.id}")
            else:
                # No change or GEPA couldn't parse - use SR's answer
                result = sr_result
                answer = sr_answer
                if gepa_answer is None:
                    print(f"GEPA couldn't parse answer, using SR: {sr_answer} for {ex.id}")
                else:
                    print(f"GEPA no change, using SR: {sr_answer} for {ex.id}")
            
            # Calculate total tokens for both stages
            total_input_tokens = sr_tokens + gepa_tokens
            total_output_tokens = _tok(sr_result.usage, "output_tokens", 0) + _tok(gepa_result.usage, "output_tokens", 0)
            total_tokens_all_calls = total_input_tokens + total_output_tokens
            
            # Calculate total latency
            total_latency = sr_result.latency_sec + gepa_result.latency_sec
            
            # Store both outputs for analysis
            sr_output = sr_result.text
            gepa_output = gepa_result.text
                
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Format linter: mark non-compliant outputs as incorrect even if letter is right
        format_compliant = True
        if answer is not None:
            # Check if the final line follows the exact format
            lines = result.text.strip().split('\n')
            if lines:
                final_line = lines[-1].strip()
                if not re.match(r'^Answer:\s*[A-J]\s*$', final_line, re.IGNORECASE):
                    format_compliant = False
                    print(f"Format violation in {ex.id}: '{final_line}'")
        
        is_correct = 1 if (answer == ex.answer and format_compliant) else 0
        correct += is_correct
        
        # Handle token accounting based on strategy
        if strategy == "self_refine":
            # Use total tokens from both calls for Self-Refine
            tokens_out = total_tokens_all_calls
            usage_data = {
                "call1": r1.usage, 
                "call2": r2.usage,
                "total_input_tokens": total_in,
                "total_output_tokens": total_out,
                "total_tokens_all_calls": total_tokens_all_calls,
            }
            latency_sec = total_latency
        elif strategy == "distill_from_self_refine":
            # Use total tokens from all four calls for distillation
            tokens_out = total_tokens_all_calls
            usage_data = {
                "call1": r1.usage,
                "call2": r2.usage,
                "distillation": distill_result.usage,
                "final": result.usage,
                "total_input_tokens": total_in,
                "total_output_tokens": total_out,
                "total_tokens_all_calls": total_tokens_all_calls,
            }
            latency_sec = total_latency
        elif strategy == "hybrid":
            # Use total tokens from both SR and GEPA calls for hybrid
            tokens_out = total_tokens_all_calls
            usage_data = {
                "sr_call": sr_result.usage,
                "gepa_call": gepa_result.usage,
                "sr_output": sr_output,
                "gepa_output": gepa_output,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens_all_calls": total_tokens_all_calls,
                "gepa_confidence": gepa_confidence,  # PHASE 3.4: Log confidence for analysis
            }
            latency_sec = total_latency
        else:
            # Single call for baseline/GEPA
            if isinstance(result.usage, dict):
                tokens_out = result.usage.get("output_tokens") or result.usage.get("total_tokens", 0)
            else:
                tokens_out = 0
            usage_data = result.usage
            latency_sec = result.latency_sec
        
        rows.append({
            "id": ex.id,
            "answer_gold": ex.answer,
            "answer_pred": answer,
            "correct": is_correct,
            "latency_sec": latency_sec,
            "usage": usage_data,
            "raw_text": result.text,
            "prompt_rendered": sr_prompt if strategy == "hybrid" else rendered
        })
        
        latency_list.append(latency_sec)
        if tokens_out is not None:
            tokens_list.append(tokens_out)
    
    acc = correct / len(examples) if examples else 0.0
    avg_tokens = statistics.mean(tokens_list) if tokens_list else None
    avg_latency = statistics.mean(latency_list) if latency_list else 0.0
    rec_path = pathlib.Path(out_dir) / "records.jsonl"
    write_jsonl(rec_path, rows)
    
    return EvalResult(
        accuracy=acc, 
        avg_tokens_out=avg_tokens, 
        avg_latency_sec=avg_latency, 
        records_path=str(rec_path)
    )
