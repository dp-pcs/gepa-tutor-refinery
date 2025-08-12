# Progress Tracking - GEPA Tutor Refinery

## Project Overview
**Goal**: Implement a GEPA-style prompt refinement pipeline for AI tutoring that maximizes learning accuracy while controlling cost/latency.

**Core Concept**: Run → Reflect on failures → Propose prompt edits → A/B test → Pareto-select → Iterate

## Current Status
- [x] Repository initialized and pushed to GitHub
- [x] Code structure reviewed and understood
- [x] Progress tracking document created

## Architecture Understanding

### Core Components
1. **Main Loop** (`src/run_loop.py`): Orchestrates the entire pipeline
2. **Evaluator** (`src/evaluator.py`): Runs MCQ evaluations with different strategies
3. **Reflection Engine** (`src/reflect_and_edit.py`): Analyzes failures and proposes prompt edits
4. **Pareto Selection** (`src/pareto.py`): Identifies non-dominated prompt variants
5. **Model Providers** (`src/models/`): Interface with OpenAI, Anthropic, or mock models

### Evaluation Strategies
- **Baseline**: Single-shot tutor prompt
- **Self-Refine**: Iterative self-feedback (prompt-only)
- **GEPA**: Full reflection → edit → evaluate → Pareto select loop

### Datasets Supported
- **Synthetic**: Included offline dataset for smoke tests
- **RACE**: Reading comprehension MCQ (middle/high school)
- **ARC**: Grade-school science MCQ (Easy/Challenge variants)

## Immediate Next Steps

### 1. Environment Setup
- [x] Create virtual environment
- [x] Install dependencies
- [x] Verify Python 3.10+ compatibility

### 2. Initial Smoke Test
- [ ] Run synthetic dataset baseline
- [ ] Verify mock model functionality
- [ ] Check output format and logging

### 3. Core Pipeline Validation
- [ ] Test GEPA loop with synthetic data
- [ ] Verify reflection and prompt editing
- [ ] Validate Pareto frontier selection

### 4. Real Dataset Integration
- [ ] Test with RACE dataset
- [ ] Test with ARC dataset
- [ ] Verify data loading and preprocessing

## Questions & Clarifications Needed

### Technical Questions
1. **Model Integration**: Should we test with real API keys or stick to mock for development?
2. **Dataset Size**: Are the default dataset sizes (30 train, 10 dev, 10 test) sufficient for meaningful evaluation?
3. **Error Handling**: How robust is the current error handling for API failures?

### Business Logic Questions
1. **Prompt Edits**: How many prompt edits per round is optimal? (Currently set to 3)
2. **Reflection Examples**: How many failed examples should be used for reflection? (Currently 20)
3. **Iteration Count**: Should we increase max_rounds beyond 2 for more thorough optimization?

## Issues & Concerns

### Potential Issues Identified
1. **Token Counting**: The evaluator has some complexity around token counting that might be fragile
2. **JSON Parsing**: Reflection responses need to be valid JSON - this could fail silently
3. **Data Validation**: Limited validation of dataset format consistency

### Performance Considerations
1. **API Rate Limits**: Need to handle potential rate limiting gracefully
2. **Cost Management**: No built-in cost tracking or limits
3. **Parallelization**: Currently sequential evaluation - could be slow for large datasets

## Test Plan

### Phase 1: Basic Functionality
- [ ] Mock model evaluation
- [ ] Synthetic dataset processing
- [ ] Basic prompt evaluation

### Phase 2: GEPA Pipeline
- [ ] Failure collection and analysis
- [ ] Prompt editing and variant generation
- [ ] Pareto frontier selection

### Phase 3: Real Models
- [ ] OpenAI integration
- [ ] Anthropic integration
- [ ] Performance benchmarking

### Phase 4: Dataset Validation
- [ ] RACE dataset integration
- [ ] ARC dataset integration
- [ ] Cross-dataset generalization

## Success Metrics
- [ ] All three evaluation modes working
- [ ] GEPA loop producing measurable improvements
- [ ] Pareto selection identifying optimal variants
- [ ] Comprehensive logging and reporting
- [ ] Reproducible results across runs

## Notes & Observations
*Document any insights, unexpected behaviors, or important findings here*

---

**Last Updated**: [Current Date]
**Status**: Ready to begin implementation
**Next Action**: Environment setup and initial smoke test
