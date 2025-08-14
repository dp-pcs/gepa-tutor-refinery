# Phase 4 Quick Reference: Advanced Hybrid Features

**Status:** Implementation Planning  
**Baseline:** Phase 3.4 (Threshold 0.85, LSAT-LR 40% accuracy)

## 🚀 Implementation Priority Matrix

| Feature | Priority | Status | Effort | Risk | Impact |
|---------|----------|--------|--------|------|---------|
| **Context-Aware GEPA** | 🔴 HIGH | Ready | 2-3 days | Low | High |
| **Override Reason Logging** | 🔴 HIGH | Ready | 1-2 days | Low | High |
| **Multi-Pass Validation** | 🟡 MEDIUM | Design | 3-4 days | Medium | Medium |
| **Weighted Confidence Scoring** | 🟡 MEDIUM | Design | 4-5 days | Medium-High | High |
| **Cost-Aware Execution** | 🟢 LOW | Design | 5-6 days | High | Medium |

## 📋 Feature Summary

### 1. Context-Aware GEPA
- **What:** Domain-specific auditor prompts
- **Why:** Generic review steps aren't optimal across domains
- **How:** Swap prompts based on dataset (TruthfulQA, LSAT-LR, GPQA)
- **Status:** Ready for implementation

### 2. Override Reason Logging
- **What:** Track why overrides were attempted/rejected
- **Why:** Enable debugging without rerunning full datasets
- **How:** Log decision reasons, confidence scores, reasoning snippets
- **Status:** Ready for implementation

### 3. Multi-Pass Validation
- **What:** Second lightweight validation for high-confidence overrides
- **Why:** Avoid "confidently wrong" overrides
- **How:** Ultra-short prompt to re-check answer choice
- **Status:** Design phase

### 4. Weighted Confidence Scoring
- **What:** Dynamic thresholds based on multiple factors
- **Why:** Different datasets justify different aggressiveness
- **How:** Combine GEPA confidence, SR certainty, reasoning agreement
- **Status:** Design phase

### 5. Cost-Aware Execution
- **What:** Dynamic execution strategy selection
- **Why:** Further reduce tokens per correct answer
- **How:** Skip GEPA on easy questions, choose strategy by difficulty
- **Status:** Design phase

## 🎯 Success Targets

### Primary Metrics
- **Accuracy Improvement:** +5-10% over Phase 3.4 baseline
- **Cost Reduction:** -10-20% tokens per correct answer
- **Override Success Rate:** >80% for high-confidence overrides

### Secondary Metrics
- **Debugging Capability:** Identify and fix override issues
- **Domain Adaptation:** Performance improvement across datasets
- **False Positive Reduction:** Fewer incorrect overrides

## 📅 Implementation Timeline

### Week 1: Foundation
- **Days 1-2:** Context-Aware GEPA
- **Days 3-4:** Override Reason Logging
- **Day 5:** Testing and validation

### Week 2: Advanced Features
- **Days 1-3:** Multi-Pass Validation
- **Days 4-5:** Testing and refinement

### Week 3: Dynamic Features
- **Days 1-3:** Weighted Confidence Scoring
- **Days 4-5:** Testing and validation

### Week 4: Cost Optimization
- **Days 1-3:** Cost-Aware Execution
- **Days 4-5:** Comprehensive testing

## 🔧 Technical Implementation

### Key Classes to Add
```python
# Phase 4.1: Context-Aware GEPA
def get_domain_specific_gepa_prompt(dataset_name: str, question: str, choices: str) -> str

# Phase 4.2: Override Reason Logging
class OverrideDecision:
    # Track override decisions with reasons

# Phase 4.3: Multi-Pass Validation
def multi_pass_validation(sr_result, gepa_result, confidence, threshold, example_id)

# Phase 4.4: Weighted Confidence Scoring
class WeightedConfidenceScorer:
    # Calculate dynamic confidence scores

# Phase 4.5: Cost-Aware Execution
class CostAwareExecutor:
    # Choose execution strategy dynamically
```

### Configuration Updates
```yaml
# Add to threshold_experiments.yaml
phase4:
  context_aware_gepa:
    enabled: true
    domain_prompts:
      truthfulqa_official: "fact-checking auditor"
      lsat_lr: "logical reasoning auditor"
      gpqa_diamond: "calculation verification auditor"
  
  override_logging:
    enabled: true
    detailed_reasons: true
  
  multi_pass_validation:
    enabled: false  # Phase 4.3
    second_pass_threshold: 0.90
  
  weighted_scoring:
    enabled: false  # Phase 4.4
    weights:
      gepa_confidence: 0.6
      sr_certainty: 0.2
      reasoning_agreement: 0.15
      domain_factor: 0.05
  
  cost_aware_execution:
    enabled: false  # Phase 4.5
    skip_threshold: 0.3
```

## 🧪 Testing Strategy

### Phase 4.1: Context-Aware GEPA
1. **Baseline comparison** against generic prompts
2. **Domain-specific validation** for each dataset
3. **Performance metrics** (accuracy, override success rate)

### Phase 4.2: Override Reason Logging
1. **Logging completeness** - all overrides tracked
2. **Reason categorization** - proper tagging of override reasons
3. **Metrics generation** - override analysis reports

### Phase 4.3: Multi-Pass Validation
1. **False positive reduction** - measure incorrect override reduction
2. **Cost impact** - additional token usage
3. **Accuracy improvement** - overall performance impact

### Phase 4.4: Weighted Confidence Scoring
1. **Dynamic threshold effectiveness** - performance vs. static thresholds
2. **Factor contribution** - which factors matter most
3. **Dataset adaptation** - performance across different domains

### Phase 4.5: Cost-Aware Execution
1. **Strategy selection accuracy** - correct strategy chosen
2. **Cost reduction** - tokens saved vs. accuracy maintained
3. **Execution efficiency** - overall performance impact

## 🚨 Risk Mitigation

### Technical Risks
- **Complexity Increase:** Implement features incrementally
- **Performance Impact:** Monitor latency and token usage
- **Integration Issues:** Thorough testing at each stage

### Operational Risks
- **Metrics Tracking:** Ensure all new metrics are properly logged
- **Configuration Management:** Version control all changes
- **Rollback Plan:** Maintain ability to revert to Phase 3.4 baseline

## 📚 Documentation

### Implementation Guides
- **`PHASE_4_IMPLEMENTATION_GUIDE.md`** - Comprehensive implementation details
- **`THRESHOLD_OPTIMIZATION_README.md`** - Updated with Phase 4 roadmap
- **`report/threshold_experiment_summary.md`** - Phase 3.4 baseline results

### Configuration Files
- **`configs/threshold_experiments.yaml`** - Main configuration
- **`configs/threshold_075.yaml`** - 0.75 threshold config
- **`configs/threshold_080.yaml`** - 0.80 threshold config
- **`configs/threshold_085.yaml`** - 0.85 threshold config (optimal)

### Scripts
- **`scripts/run_threshold_experiments.py`** - Single dataset experiments
- **`scripts/run_multi_dataset_threshold_experiments.py`** - Multi-dataset experiments
- **`scripts/analyze_threshold_results.py`** - Results analysis

## 🎉 Success Criteria

### Phase 4.1 Complete
- [ ] Context-Aware GEPA implemented
- [ ] Domain-specific prompts working
- [ ] Performance improved over generic prompts

### Phase 4.2 Complete
- [ ] Override reason logging implemented
- [ ] All overrides tracked with reasons
- [ ] Analysis reports generated

### Phase 4.3 Complete
- [ ] Multi-pass validation implemented
- [ ] False positive reduction achieved
- [ ] Cost impact acceptable

### Phase 4.4 Complete
- [ ] Weighted confidence scoring implemented
- [ ] Dynamic thresholds working
- [ ] Performance improved over static thresholds

### Phase 4.5 Complete
- [ ] Cost-aware execution implemented
- [ ] Token reduction achieved
- [ ] Accuracy maintained or improved

## 🔄 Iteration Plan

1. **Implement Phase 4.1** (Context-Aware GEPA)
2. **Test and validate** against baseline
3. **Implement Phase 4.2** (Override Reason Logging)
4. **Test and validate** both features
5. **Continue incrementally** through remaining features
6. **Comprehensive testing** of all Phase 4 features
7. **Performance analysis** and optimization
8. **Documentation update** with final results

## 📞 Support

For questions or issues during Phase 4 implementation:
1. **Check documentation** - Start with this quick reference
2. **Review implementation guide** - Detailed technical specifications
3. **Examine baseline results** - Phase 3.4 performance metrics
4. **Test incrementally** - Validate each feature before moving to next
5. **Monitor metrics** - Track performance impact of each feature
