# Threshold Optimization System for Hybrid SR → GEPA

This document describes the enhanced threshold management system that allows fine-tuning of confidence thresholds and conditional GEPA execution for the hybrid Self-Refine → GEPA approach.

## Overview

The threshold optimization system addresses the key challenge identified in previous experiments: **finding the sweet spot between GEPA override success rate and overall accuracy**. The system provides:

1. **Fine-tuned confidence thresholds** (0.75, 0.80, 0.85, etc.)
2. **Conditional GEPA execution** based on uncertainty signals
3. **Dataset-specific threshold optimization**
4. **Comprehensive reporting and analysis**

## Key Features

### 1. Configurable Confidence Thresholds

- **Default thresholds**: 0.75, 0.80, 0.85
- **Dataset-specific thresholds**: Custom thresholds for different datasets
- **Dynamic threshold loading**: Thresholds can be changed without code modification

### 2. Conditional GEPA Execution

The system can skip GEPA execution when:
- **Uncertainty signals** are detected in SR output (e.g., "maybe", "uncertain", "I think")
- **Length anomalies** occur (too short or too long)
- **Reasoning structure** is missing (no logical connectors)

### 3. Enhanced Safety Checks

- **Explicit invalidation required**: GEPA must explicitly flag SR as incorrect
- **Configurable keywords**: Customizable invalidation language
- **Confidence scoring**: Multi-factor confidence calculation

## Configuration

### Main Configuration File: `configs/threshold_experiments.yaml`

```yaml
# Threshold experiment configuration
thresholds:
  # Default confidence thresholds
  confidence_levels: [0.75, 0.80, 0.85]
  
  # Dataset-specific thresholds
  dataset_specific:
    truthfulqa_official: [0.80, 0.85, 0.90]  # More aggressive
    gpqa_diamond: [0.80, 0.85, 0.90]         # More aggressive
    agieval_lsat_lr: [0.85, 0.90, 0.95]      # Ultra-conservative
    agieval_lsat_ar: [0.80, 0.85, 0.90]      # Conservative
    agieval_sat_math: [0.80, 0.85, 0.90]     # Conservative
    mmlu_pro: [0.80, 0.85, 0.90]             # Conservative
    logiqa2: [0.80, 0.85, 0.90]              # Conservative

# Conditional GEPA execution
conditional_gepa:
  enabled: true
  
  # Uncertainty signals that trigger GEPA skip
  uncertainty_signals:
    - "maybe"
    - "uncertain"
    - "not sure"
    - "could be"
    - "might be"
    - "possibly"
    - "I think"
    - "I believe"
    - "seems like"
    - "appears to"
  
  # Length thresholds for GEPA skip
  length_thresholds:
    min_tokens: 30   # Skip if too short
    max_tokens: 200  # Skip if too long
  
  # Reasoning structure indicators
  reasoning_indicators:
    - "because"
    - "since"
    - "as"
    - "due to"
    - "reason"
    - "logic"
    - "therefore"
    - "thus"
    - "hence"

# Explicit invalidation requirements
explicit_invalidation:
  required: true
  keywords:
    - "incorrect"
    - "wrong"
    - "not supported"
    - "invalid"
    - "false"
    - "misleading"
    - "unsupported"
    - "factually wrong"
    - "logically flawed"
    - "error"
    - "mistake"
```

## Usage

### 1. Single Dataset Threshold Sweep

Run threshold experiments for a single dataset:

```bash
python scripts/run_threshold_experiments.py
```

This will:
- Load configuration from `configs/threshold_experiments.yaml`
- Test all configured thresholds for the specified dataset
- Generate a detailed report with results
- Provide override statistics and cost analysis

### 2. Multi-Dataset Threshold Experiments

Run threshold experiments across all configured datasets:

```bash
python scripts/run_multi_dataset_threshold_experiments.py
```

This will:
- Test all datasets with their specific threshold ranges
- Generate comprehensive cross-dataset analysis
- Identify optimal thresholds for each dataset
- Provide cross-dataset insights and recommendations

### 3. Manual Threshold Testing

Test a specific threshold manually:

```bash
# Create a custom config with specific threshold
python -m src.run_loop --config configs/threshold_experiments.yaml --mode hybrid
```

## Output and Analysis

### 1. Individual Experiment Reports

Each threshold experiment generates:
- **Accuracy metrics**: Dev and test accuracy
- **Token usage**: Average tokens per example
- **Override statistics**: Number of GEPA overrides and success rate
- **GEPA skip rate**: Percentage of examples where GEPA was skipped
- **Cost analysis**: Tokens per correct answer

### 2. Comprehensive Analysis

The system provides:
- **Threshold comparison tables** across all experiments
- **Best threshold identification** for each dataset
- **Cost-benefit analysis** of different thresholds
- **Cross-dataset patterns** and insights
- **Actionable recommendations** for production deployment

### 3. Key Metrics Tracked

- **Override Success Rate**: Percentage of GEPA overrides that were correct
- **GEPA Skip Rate**: Percentage of examples where GEPA execution was skipped
- **Cost per Correct Answer**: Token cost divided by accuracy
- **Threshold Impact**: How different thresholds affect overall performance

## Example Results

### Sample Threshold Sweep Results

| Threshold | Dev Acc | Test Acc | Dev Tokens | Test Tokens | Overrides | Success Rate | GEPA Skips |
|-----------|---------|----------|------------|-------------|-----------|--------------|------------|
| 0.75 | 0.850 | 0.800 | 245.2 | 251.8 | 8 | 0.625 | 0.200 |
| 0.80 | 0.900 | 0.850 | 238.1 | 245.3 | 6 | 0.833 | 0.300 |
| 0.85 | 0.950 | 0.900 | 235.6 | 242.1 | 4 | 1.000 | 0.400 |

### Key Insights

- **Best Threshold**: 0.85 (highest test accuracy)
- **Override Success Rate**: 100% at 0.85 threshold
- **GEPA Skip Rate**: 40% at 0.85 threshold (cost optimization)
- **Cost per Correct**: 269 tokens at 0.85 threshold

## Advanced Configuration

### 1. Custom Uncertainty Signals

Add domain-specific uncertainty indicators:

```yaml
conditional_gepa:
  uncertainty_signals:
    - "maybe"
    - "uncertain"
    - "not sure"
    - "could be"
    - "might be"
    - "possibly"
    - "I think"
    - "I believe"
    - "seems like"
    - "appears to"
    # Add domain-specific signals
    - "approximately"
    - "roughly"
    - "around"
    - "about"
```

### 2. Dataset-Specific Thresholds

Optimize thresholds based on dataset characteristics:

```yaml
thresholds:
  dataset_specific:
    # Factual datasets: More aggressive thresholds
    truthfulqa_official: [0.80, 0.85, 0.90]
    gpqa_diamond: [0.80, 0.85, 0.90]
    
    # Reasoning datasets: Conservative thresholds
    agieval_lsat_lr: [0.85, 0.90, 0.95]
    agieval_lsat_ar: [0.80, 0.85, 0.90]
    
    # Mathematical datasets: Balanced thresholds
    agieval_sat_math: [0.80, 0.85, 0.90]
```

### 3. Custom Invalidation Keywords

Define domain-specific invalidation language:

```yaml
explicit_invalidation:
  keywords:
    # General invalidation
    - "incorrect"
    - "wrong"
    - "invalid"
    
    # Domain-specific invalidation
    - "mathematically impossible"
    - "logically inconsistent"
    - "factually incorrect"
    - "scientifically unsound"
```

## Troubleshooting

### Common Issues

1. **Configuration File Not Found**
   - Ensure `configs/threshold_experiments.yaml` exists
   - Check file permissions and path

2. **Threshold Experiments Fail**
   - Verify dataset names in configuration
   - Check that data setup scripts work
   - Ensure sufficient API credits for experiments

3. **No Overrides Generated**
   - Check confidence threshold values
   - Verify explicit invalidation requirements
   - Review conditional GEPA settings

### Debug Mode

Enable detailed logging by setting:

```yaml
logging:
  detailed_logging: true
```

This will log:
- All threshold decisions
- GEPA skip reasons
- Override decisions and confidence scores
- Detailed execution flow

## Best Practices

### 1. Threshold Selection

- **Start conservative**: Begin with higher thresholds (0.85+) for challenging datasets
- **Iterate gradually**: Test thresholds in 0.05 increments
- **Monitor overrides**: Ensure sufficient override examples for statistical significance
- **Balance cost and accuracy**: Consider token cost vs. accuracy improvements

### 2. Conditional GEPA Tuning

- **Uncertainty signals**: Focus on language patterns that indicate low confidence
- **Length thresholds**: Adjust based on typical SR output lengths
- **Reasoning indicators**: Ensure logical structure is preserved
- **Domain adaptation**: Customize signals for specific domains

### 3. Production Deployment

- **Validate thresholds**: Test on held-out data before production
- **Monitor performance**: Track override success rates in production
- **A/B testing**: Compare different threshold configurations
- **Gradual rollout**: Deploy changes incrementally

## Phase 4 - Advanced Hybrid Features

### 1. Context-Aware GEPA

**Goal:** Make the "auditor" adapt its review style to the dataset domain.

**Implementation:**
- **TruthfulQA:** Emphasize fact-checking & avoiding hallucinations
- **LSAT-LR:** Emphasize logic flaw detection  
- **GPQA:** Emphasize calculation verification & step-checking
- **Generic:** Fallback to current safety auditor logic

**Why:** Phase 3.4 analysis showed generic review steps aren't optimal across domains.

**Status:** Ready for implementation

### 2. Multi-Pass Validation

**Goal:** Add a second lightweight validation pass when GEPA disagrees with SR at high confidence.

**Implementation:**
- **GEPA #1:** Current safety auditor logic
- **GEPA #2:** Ultra-short prompt that just re-checks the answer choice ("Does answer X fit the evidence?")
- **Trigger:** High confidence disagreements between SR and GEPA

**Why:** Avoid "confidently wrong" overrides slipping through when confidence is high but reasoning is flawed.

**Status:** Design phase

### 3. Weighted Confidence Scoring

**Goal:** Make the threshold dynamic rather than static.

**Implementation:**
- **GEPA confidence score** (current implementation)
- **SR's "certainty" proxy** (output length, hedging language)
- **Agreement between SR and GEPA's reasoning structure**
- **Combined weighted score** for dynamic threshold decisions

**Why:** Different datasets may justify different override aggressiveness without hard-coding multiple thresholds.

**Status:** Design phase

### 4. Override Reason Logging & Metrics

**Goal:** Track why an override was attempted or rejected.

**Implementation:**
- **Save reasoning snippets** + confidence scores alongside overrides
- **Tag each override** with "explicit invalidation", "low SR confidence", "high agreement", etc.
- **Detailed metrics** for debugging and refinement

**Why:** Lets you debug and refine without rerunning full datasets.

**Status:** Ready for implementation

### 5. Cost-Aware Execution

**Goal:** Reduce average tokens per correct further without hurting accuracy.

**Implementation:**
- **Skip GEPA entirely** when SR has high-confidence wins on easy questions
- **Auto-downgrade to single-call SR** on low-value items (based on dev/test analysis)
- **Dynamic execution strategy** based on question difficulty and SR confidence

**Why:** Further optimize cost-performance trade-offs.

**Status:** Design phase

## Phase 4 Rollout Plan

### Phase 4.1: Baseline Snapshot
- **Lock in 0.85 config** and export a "before" metrics pack
- **Document current performance** as baseline for comparison
- **Prepare Phase 3.4 metrics** (accuracy, overrides, tokens per correct, success rate)

### Phase 4.2: Feature Implementation
- **Implement one feature at a time** so we can isolate effects
- **Start with Context-Aware GEPA** (highest impact, lowest risk)
- **Follow with Override Reason Logging** (enables better debugging)

### Phase 4.3: Testing & Validation
- **Run small-split tests** on TruthfulQA, LSAT-LR, GPQA for each feature
- **Compare against Phase 3.4 baseline** for easy comparison
- **Iterate based on results** before moving to next feature

### Phase 4.4: Advanced Features
- **Multi-Pass Validation** (requires careful prompt engineering)
- **Weighted Confidence Scoring** (requires algorithm development)
- **Cost-Aware Execution** (requires difficulty estimation)

## Future Enhancements

### 1. Adaptive Thresholds

- **Dynamic threshold adjustment** based on performance
- **Online learning** from production feedback
- **Contextual thresholds** based on question difficulty

### 2. Advanced Conditional Logic

- **Multi-factor decision trees** for GEPA execution
- **Confidence calibration** based on historical performance
- **Domain-specific skip conditions**

### 3. Cost Optimization

- **Token budget management** with accuracy constraints
- **Selective GEPA execution** based on expected value
- **Batch processing** optimization

## Conclusion

The threshold optimization system provides a systematic approach to finding the optimal balance between GEPA override success and overall performance. By combining configurable thresholds, conditional execution, and comprehensive analysis, it enables data-driven optimization of the hybrid SR → GEPA approach.

Key benefits:
- **Improved accuracy** through optimal threshold selection
- **Cost reduction** via conditional GEPA execution
- **Dataset-specific optimization** for maximum performance
- **Comprehensive analysis** for informed decision-making

For questions or issues, refer to the troubleshooting section or check the generated reports for detailed analysis.
