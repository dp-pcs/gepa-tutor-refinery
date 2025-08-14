# Phase 4 Implementation Guide: Advanced Hybrid Features

**Generated:** August 13, 2025  
**Status:** Implementation Planning  
**Phase:** Advanced Hybrid Features for SR → GEPA

## Overview

Phase 4 builds upon the successful threshold optimization (Phase 3.4) to implement advanced features that will further improve the hybrid SR → GEPA approach. The goal is to enhance accuracy, reduce costs, and provide better debugging capabilities while maintaining the safety-auditor mode.

## Current Baseline (Phase 3.4)

### Performance Metrics
- **Optimal Threshold:** 0.85 for LSAT-LR
- **Test Accuracy:** 40% (improved from baseline)
- **Cost per Correct:** 2142.5 tokens
- **Override Success Rate:** TBD (needs detailed analysis)
- **GEPA Skip Rate:** TBD (needs detailed analysis)

### Configuration
- **Threshold:** 0.85 (conservative)
- **Conditional GEPA:** Enabled
- **Explicit Invalidation:** Required
- **Dataset:** LSAT-LR (most challenging)

## Phase 4.1: Context-Aware GEPA

### Implementation Priority: HIGH
**Status:** Ready for implementation  
**Estimated Effort:** 2-3 days  
**Risk:** Low  

### Goal
Make the GEPA "auditor" adapt its review style to the dataset domain instead of using generic review steps.

### Current Implementation
```python
# Generic GEPA review prompt (current)
gepa_review_prompt = f"""You are reviewing an answer from a tutor for a multiple-choice question.

Task:
1) Verify the chosen answer is well-reasoned and correct.
2) If the answer is correct, confirm in <= 40 tokens.
3) If the answer is wrong, identify the correct choice with brief reasoning.
4) End with exactly: Answer: <LETTER>
"""
```

### Proposed Implementation
```python
# Domain-specific GEPA review prompts
def get_domain_specific_gepa_prompt(dataset_name: str, question: str, choices: str) -> str:
    if dataset_name == "truthfulqa_official":
        return f"""You are a **fact-checking auditor** reviewing an answer for TruthfulQA.

Task:
1) Verify the chosen answer is factually correct and avoids hallucinations.
2) Check if the answer is supported by common knowledge.
3) If correct, confirm in <= 30 tokens.
4) If wrong, identify the factually accurate choice with brief reasoning.
5) End with exactly: Answer: <LETTER>

Question: {question}
Choices: {choices}"""

    elif dataset_name == "lsat_lr":
        return f"""You are a **logical reasoning auditor** reviewing an answer for LSAT-LR.

Task:
1) Verify the chosen answer follows logically from the reasoning.
2) Check for logical flaws, unsupported assumptions, or reasoning gaps.
3) If the logic is sound, confirm in <= 30 tokens.
4) If there's a logical flaw, identify the correct choice with brief reasoning.
5) End with exactly: Answer: <LETTER>

Question: {question}
Choices: {choices}"""

    elif dataset_name == "gpqa_diamond":
        return f"""You are a **calculation verification auditor** reviewing an answer for GPQA.

Task:
1) Verify the chosen answer is mathematically correct.
2) Check if all calculation steps are valid and complete.
3) If correct, confirm in <= 30 tokens.
4) If wrong, identify the mathematically sound choice with brief reasoning.
5) End with exactly: Answer: <LETTER>

Question: {question}
Choices: {choices}"""

    else:
        # Fallback to generic prompt
        return get_generic_gepa_prompt(question, choices)
```

### Integration Points
1. **`src/evaluator.py`** - Update hybrid strategy to use domain-specific prompts
2. **`src/run_loop.py`** - Pass dataset information to evaluator
3. **Configuration files** - Add domain-specific prompt templates

### Testing Strategy
1. **Baseline comparison** - Compare against current generic prompts
2. **Domain-specific validation** - Ensure prompts are appropriate for each domain
3. **Performance metrics** - Track accuracy, override success rate, token usage

## Phase 4.2: Override Reason Logging & Metrics

### Implementation Priority: HIGH
**Status:** Ready for implementation  
**Estimated Effort:** 1-2 days  
**Risk:** Low  

### Goal
Track why an override was attempted or rejected to enable better debugging and refinement.

### Current Implementation
```python
# Basic override logging (current)
if gepa_confidence >= confidence_threshold:
    if explicit_invalidation:
        result = gepa_result
        answer = gepa_answer
        print(f"GEPA OVERRIDE (conf: {gepa_confidence:.2f}, threshold: {confidence_threshold:.2f}, explicit invalidation): {sr_answer} → {gepa_answer} for {ex.id}")
```

### Proposed Implementation
```python
# Enhanced override logging with reason tracking
class OverrideDecision:
    def __init__(self, example_id: str, sr_answer: str, gepa_answer: str, 
                 confidence: float, threshold: float, decision: str, reason: str):
        self.example_id = example_id
        self.sr_answer = sr_answer
        self.gepa_answer = gepa_answer
        self.confidence = confidence
        self.threshold = threshold
        self.decision = decision  # "OVERRIDE", "REJECT", "SKIP"
        self.reason = reason      # "explicit_invalidation", "low_confidence", "high_agreement", etc.
        self.timestamp = datetime.now()
        self.reasoning_snippet = ""  # Key reasoning text from GEPA

# Enhanced decision logic
def make_override_decision(sr_result, gepa_result, confidence, threshold, example_id):
    decision = OverrideDecision(
        example_id=example_id,
        sr_answer=parse_answer_letter(sr_result.text),
        gepa_answer=parse_answer_letter(gepa_result.text),
        confidence=confidence,
        threshold=threshold,
        decision="",
        reason=""
    )
    
    if confidence >= threshold:
        if check_explicit_invalidation(gepa_result.text):
            decision.decision = "OVERRIDE"
            decision.reason = "explicit_invalidation"
            decision.reasoning_snippet = extract_key_reasoning(gepa_result.text)
        else:
            decision.decision = "REJECT"
            decision.reason = "no_explicit_invalidation"
    else:
        decision.decision = "REJECT"
        decision.reason = "below_threshold"
    
    return decision

# Logging and metrics
def log_override_decision(decision: OverrideDecision, records: List[Dict]):
    records.append({
        "id": decision.example_id,
        "override_decision": decision.decision,
        "override_reason": decision.reason,
        "confidence": decision.confidence,
        "threshold": decision.threshold,
        "sr_answer": decision.sr_answer,
        "gepa_answer": decision.gepa_answer,
        "reasoning_snippet": decision.reasoning_snippet,
        "timestamp": decision.timestamp.isoformat()
    })
```

### Integration Points
1. **`src/evaluator.py`** - Add OverrideDecision class and logging
2. **`src/run_loop.py`** - Collect and store override decisions
3. **Reporting scripts** - Generate override reason analysis

### Metrics to Track
1. **Override Success Rate by Reason** - Which reasons lead to successful overrides?
2. **Confidence Distribution by Reason** - How confident is GEPA for different reasons?
3. **Reasoning Quality** - Are explicit invalidations actually valid?
4. **Cost Analysis by Reason** - Which override reasons are most cost-effective?

## Phase 4.3: Multi-Pass Validation

### Implementation Priority: MEDIUM
**Status:** Design phase  
**Estimated Effort:** 3-4 days  
**Risk:** Medium  

### Goal
Add a second lightweight validation pass when GEPA disagrees with SR at high confidence to avoid "confidently wrong" overrides.

### Design
```python
# Multi-pass validation logic
def multi_pass_validation(sr_result, gepa_result, confidence, threshold, example_id):
    # First pass: Current safety auditor logic
    first_pass_decision = make_override_decision(sr_result, gepa_result, confidence, threshold, example_id)
    
    # Second pass: Only if first pass suggests override at high confidence
    if (first_pass_decision.decision == "OVERRIDE" and 
        confidence >= threshold + 0.05):  # Higher threshold for second pass
        
        # Ultra-short validation prompt
        validation_prompt = f"""Quick validation: Does answer {gepa_result.answer} fit the evidence?

Question: {question}
SR Answer: {sr_result.answer}
GEPA Answer: {gepa_result.answer}

Answer only: YES or NO"""

        validation_result = provider.generate(validation_prompt)
        
        if "NO" in validation_result.text.upper():
            # Second pass rejected the override
            first_pass_decision.decision = "REJECT"
            first_pass_decision.reason = "second_pass_rejection"
            first_pass_decision.reasoning_snippet += f" | Second pass: {validation_result.text}"
    
    return first_pass_decision
```

### Integration Points
1. **`src/evaluator.py`** - Add multi-pass validation logic
2. **Configuration** - Add second-pass threshold and prompt settings
3. **Metrics** - Track second-pass rejection rates

### Testing Strategy
1. **False positive reduction** - Measure reduction in incorrect overrides
2. **Cost impact** - Measure additional token usage for second pass
3. **Accuracy improvement** - Overall accuracy impact

## Phase 4.4: Weighted Confidence Scoring

### Implementation Priority: MEDIUM
**Status:** Design phase  
**Estimated Effort:** 4-5 days  
**Risk:** Medium-High  

### Goal
Make the threshold dynamic by combining multiple factors into a weighted confidence score.

### Design
```python
# Weighted confidence scoring
class WeightedConfidenceScorer:
    def __init__(self, weights: Dict[str, float]):
        self.weights = weights
    
    def calculate_weighted_confidence(self, 
                                    gepa_confidence: float,
                                    sr_certainty: float,
                                    reasoning_agreement: float,
                                    domain_factor: float) -> float:
        """
        Calculate weighted confidence score from multiple factors
        """
        weighted_score = (
            self.weights['gepa_confidence'] * gepa_confidence +
            self.weights['sr_certainty'] * sr_certainty +
            self.weights['reasoning_agreement'] * reasoning_agreement +
            self.weights['domain_factor'] * domain_factor
        )
        
        return min(weighted_score, 1.0)
    
    def estimate_sr_certainty(self, sr_output: str) -> float:
        """Estimate SR's certainty based on output characteristics"""
        certainty = 0.5  # Base certainty
        
        # Length factor (optimal length = higher certainty)
        optimal_length = 100
        actual_length = len(sr_output.split())
        length_factor = 1.0 - abs(actual_length - optimal_length) / optimal_length
        certainty += 0.2 * length_factor
        
        # Hedging language factor
        hedging_words = ["maybe", "uncertain", "not sure", "could be", "might be"]
        hedging_count = sum(1 for word in hedging_words if word in sr_output.lower())
        hedging_factor = max(0, 1.0 - hedging_count * 0.2)
        certainty += 0.2 * hedging_factor
        
        # Reasoning structure factor
        reasoning_words = ["because", "since", "as", "due to", "therefore", "thus"]
        reasoning_count = sum(1 for word in reasoning_words if word in sr_output.lower())
        reasoning_factor = min(1.0, reasoning_count * 0.15)
        certainty += 0.1 * reasoning_factor
        
        return max(0.0, min(1.0, certainty))
    
    def calculate_reasoning_agreement(self, sr_output: str, gepa_output: str) -> float:
        """Calculate agreement between SR and GEPA reasoning structures"""
        # Extract key concepts and reasoning patterns
        sr_concepts = extract_key_concepts(sr_output)
        gepa_concepts = extract_key_concepts(gepa_output)
        
        # Calculate overlap
        overlap = len(sr_concepts.intersection(gepa_concepts))
        total = len(sr_concepts.union(gepa_concepts))
        
        return overlap / total if total > 0 else 0.0

# Dynamic threshold adjustment
def get_dynamic_threshold(base_threshold: float, 
                         dataset_name: str, 
                         question_difficulty: float) -> float:
    """Adjust threshold based on dataset and question difficulty"""
    
    # Dataset-specific adjustments
    dataset_adjustments = {
        "truthfulqa_official": 0.0,    # More aggressive
        "gpqa_diamond": 0.0,          # More aggressive
        "agieval_lsat_lr": 0.05,      # More conservative
        "agieval_lsat_ar": 0.02,      # Slightly conservative
        "agieval_sat_math": 0.0,      # Balanced
    }
    
    # Difficulty adjustments
    difficulty_adjustment = question_difficulty * 0.1  # Harder questions = higher threshold
    
    adjusted_threshold = base_threshold + dataset_adjustments.get(dataset_name, 0.0) + difficulty_adjustment
    
    return min(adjusted_threshold, 0.95)  # Cap at 0.95
```

### Integration Points
1. **`src/evaluator.py`** - Add WeightedConfidenceScorer class
2. **Configuration** - Add weights and adjustment factors
3. **Metrics** - Track dynamic threshold effectiveness

## Phase 4.5: Cost-Aware Execution

### Implementation Priority: LOW
**Status:** Design phase  
**Estimated Effort:** 5-6 days  
**Risk:** High  

### Goal
Reduce average tokens per correct answer further without hurting accuracy by dynamically choosing execution strategy.

### Design
```python
# Cost-aware execution strategy
class CostAwareExecutor:
    def __init__(self, cost_thresholds: Dict[str, float]):
        self.cost_thresholds = cost_thresholds
    
    def choose_execution_strategy(self, 
                                question_difficulty: float,
                                sr_confidence: float,
                                expected_value: float) -> str:
        """
        Choose execution strategy based on cost-benefit analysis
        """
        
        # High-confidence easy questions: Skip GEPA entirely
        if (sr_confidence >= 0.9 and 
            question_difficulty <= 0.3 and 
            expected_value <= self.cost_thresholds['skip_threshold']):
            return "SR_ONLY"
        
        # Medium-confidence questions: Use hybrid approach
        elif sr_confidence >= 0.7:
            return "HYBRID"
        
        # Low-confidence questions: Use hybrid with higher threshold
        else:
            return "HYBRID_CONSERVATIVE"
    
    def estimate_question_difficulty(self, question: str, context: str) -> float:
        """Estimate question difficulty based on characteristics"""
        difficulty = 0.5  # Base difficulty
        
        # Length factors
        question_length = len(question.split())
        context_length = len(context.split()) if context else 0
        
        if question_length > 50:
            difficulty += 0.2
        if context_length > 200:
            difficulty += 0.2
        
        # Complexity indicators
        complexity_words = ["explain", "analyze", "compare", "evaluate", "justify"]
        complexity_count = sum(1 for word in complexity_words if word in question.lower())
        difficulty += complexity_count * 0.1
        
        # Domain-specific factors
        if "logical" in question.lower() or "reasoning" in question.lower():
            difficulty += 0.1
        if "calculate" in question.lower() or "compute" in question.lower():
            difficulty += 0.1
        
        return max(0.0, min(1.0, difficulty))
    
    def calculate_expected_value(self, 
                               question_difficulty: float,
                               dataset_value: float) -> float:
        """Calculate expected value of running GEPA"""
        
        # Higher difficulty = higher expected value
        difficulty_value = question_difficulty * 0.5
        
        # Dataset-specific value
        dataset_values = {
            "truthfulqa_official": 0.8,  # High value (factual accuracy)
            "gpqa_diamond": 0.9,         # Very high value (calculation verification)
            "agieval_lsat_lr": 0.7,      # Medium-high value (logic verification)
            "agieval_lsat_ar": 0.6,      # Medium value
            "agieval_sat_math": 0.8,     # High value (math verification)
        }
        
        dataset_value = dataset_values.get(dataset_name, 0.5)
        
        return (difficulty_value + dataset_value) / 2
```

### Integration Points
1. **`src/evaluator.py`** - Add CostAwareExecutor class
2. **Configuration** - Add cost thresholds and value factors
3. **Metrics** - Track execution strategy effectiveness

## Implementation Timeline

### Week 1: Foundation
- **Day 1-2:** Implement Context-Aware GEPA
- **Day 3-4:** Implement Override Reason Logging
- **Day 5:** Testing and validation

### Week 2: Advanced Features
- **Day 1-3:** Implement Multi-Pass Validation
- **Day 4-5:** Testing and refinement

### Week 3: Dynamic Features
- **Day 1-3:** Implement Weighted Confidence Scoring
- **Day 4-5:** Testing and validation

### Week 4: Cost Optimization
- **Day 1-3:** Implement Cost-Aware Execution
- **Day 4-5:** Comprehensive testing and documentation

## Success Metrics

### Primary Metrics
1. **Accuracy Improvement** - Target: +5-10% over Phase 3.4 baseline
2. **Cost Reduction** - Target: -10-20% tokens per correct answer
3. **Override Success Rate** - Target: >80% for high-confidence overrides

### Secondary Metrics
1. **Debugging Capability** - Ability to identify and fix override issues
2. **Domain Adaptation** - Performance improvement across different datasets
3. **False Positive Reduction** - Fewer incorrect overrides

## Risk Mitigation

### Technical Risks
1. **Complexity Increase** - Implement features incrementally
2. **Performance Impact** - Monitor latency and token usage
3. **Integration Issues** - Thorough testing at each stage

### Operational Risks
1. **Metrics Tracking** - Ensure all new metrics are properly logged
2. **Configuration Management** - Version control all configuration changes
3. **Rollback Plan** - Maintain ability to revert to Phase 3.4 baseline

## Conclusion

Phase 4 represents a significant evolution of the hybrid SR → GEPA approach, moving from static threshold optimization to dynamic, context-aware execution. The implementation plan prioritizes high-impact, low-risk features first, followed by more complex optimizations.

The key to success will be:
1. **Incremental implementation** - One feature at a time
2. **Thorough testing** - Validate each feature before moving to the next
3. **Metrics-driven decisions** - Use data to guide implementation choices
4. **Maintainable code** - Ensure new features integrate cleanly with existing system

By following this plan, we can achieve significant improvements in accuracy, cost efficiency, and debugging capability while maintaining the safety and reliability of the current system.
