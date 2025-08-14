# Changelog

All notable changes to Tutor Refinery will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 4 advanced hybrid features planning and documentation
- Comprehensive contributing guidelines
- Enhanced project documentation and organization

### Changed
- Repository cleanup and organization for public publication
- Updated README with comprehensive project overview
- Moved technical documentation to docs/ directory

## [0.2.0] - 2024-08-13

### Added
- **Phase 3.4: Threshold Optimization System**
  - Configurable confidence thresholds (0.75, 0.80, 0.85, 0.83, 0.87)
  - Dataset-specific threshold optimization
  - Conditional GEPA execution based on uncertainty signals
  - Enhanced safety checks with explicit invalidation requirements
  - Comprehensive threshold experiment automation

- **Advanced Configuration Management**
  - `threshold_experiments.yaml` - Main configuration file
  - Individual threshold configs for systematic testing
  - Dataset-specific threshold recommendations
  - Conditional GEPA execution parameters

- **Experiment Automation Scripts**
  - `run_threshold_experiments.py` - Single dataset threshold sweeps
  - `run_multi_dataset_threshold_experiments.py` - Cross-dataset validation
  - `analyze_threshold_results.py` - Results analysis and metrics
  - `confidence_distribution_analysis.py` - Confidence score analysis

- **Performance Improvements**
  - Achieved 40% test accuracy on LSAT-LR (vs. baseline ~20%)
  - Reduced cost per correct answer to 2142.5 tokens (optimal threshold)
  - Conditional GEPA execution reduces unnecessary token usage
  - Smart override decisions based on confidence and validation

### Changed
- **Enhanced Evaluator Logic**
  - Integrated threshold configuration system
  - Added conditional GEPA execution logic
  - Enhanced override decision making with confidence thresholds
  - Improved logging and metrics tracking

- **Updated Run Loop**
  - Threshold configuration loading and validation
  - Enhanced hybrid mode with threshold-aware execution
  - Improved error handling and logging

- **Configuration Structure**
  - Centralized threshold management
  - Dataset-specific optimization parameters
  - Flexible conditional execution settings

### Fixed
- GEPA override success rate issues through threshold optimization
- Confidence scoring accuracy and reliability
- Token usage optimization through conditional execution
- Safety validation for override decisions

## [0.1.0] - 2024-08-12

### Added
- **Core Hybrid Architecture**
  - Self-Refine (SR) → GEPA Review pipeline
  - Baseline evaluation modes
  - Comprehensive evaluation framework

- **Dataset Support**
  - AGIEval LSAT-LR, LSAT-AR, SAT-Math
  - TruthfulQA, GPQA-Diamond, MMLU-Pro
  - LogiQA 2.0 and synthetic datasets

- **Model Integration**
  - OpenAI GPT models support
  - Anthropic Claude models support
  - Mock client for testing and development

- **Basic Evaluation System**
  - Accuracy metrics calculation
  - Token usage tracking
  - Cost analysis and reporting
  - Basic result logging

### Changed
- Initial implementation of hybrid SR → GEPA approach
- Basic confidence scoring and override logic
- Simple configuration management

### Fixed
- Basic evaluation pipeline functionality
- Model integration and error handling
- Dataset loading and processing

## [0.0.1] - 2024-08-11

### Added
- Initial project structure
- Basic README and documentation
- License and contribution guidelines
- Project setup and dependencies

---

## Version History

- **0.0.1**: Initial project setup and structure
- **0.1.0**: Core hybrid architecture and basic evaluation system
- **0.2.0**: Threshold optimization system and performance improvements
- **Unreleased**: Phase 4 advanced features and public publication preparation

## Upcoming Releases

### [0.3.0] - Phase 4.1: Context-Aware GEPA
- Domain-specific auditor prompts
- Dataset-optimized review strategies
- Enhanced accuracy through specialization

### [0.4.0] - Phase 4.2: Override Reason Logging
- Comprehensive override decision tracking
- Detailed metrics and analysis
- Debugging and refinement tools

### [0.5.0] - Phase 4.3: Multi-Pass Validation
- Second validation pass for high-confidence overrides
- Enhanced safety and reliability
- Reduced false positive overrides

### [0.6.0] - Phase 4.4: Weighted Confidence Scoring
- Dynamic threshold algorithms
- Multi-factor confidence assessment
- Adaptive threshold management

### [0.7.0] - Phase 4.5: Cost-Aware Execution
- Dynamic execution strategy selection
- Intelligent resource allocation
- Optimal cost-accuracy trade-offs

---

## Migration Guide

### From 0.1.0 to 0.2.0

The threshold optimization system introduces significant changes to configuration and execution:

1. **Update Configuration Files**
   - Use `threshold_experiments.yaml` for new experiments
   - Configure dataset-specific thresholds
   - Enable conditional GEPA execution

2. **Update Script Usage**
   - Use new threshold experiment scripts
   - Leverage automated threshold sweeps
   - Analyze results with enhanced metrics

3. **Review Threshold Settings**
   - Start with 0.85 threshold for LSAT-LR
   - Use dataset-specific recommendations
   - Monitor override success rates

### From 0.0.1 to 0.1.0

The hybrid architecture introduces new evaluation modes:

1. **Update Run Commands**
   - Use `--mode hybrid` for SR → GEPA pipeline
   - Configure appropriate thresholds
   - Monitor both accuracy and cost metrics

2. **Review Results**
   - Compare hybrid vs. baseline performance
   - Analyze override patterns and success rates
   - Optimize thresholds for your use case

---

## Deprecation Notices

### Version 0.3.0 (Planned)
- Deprecate basic confidence scoring in favor of weighted scoring
- Deprecate static thresholds in favor of dynamic algorithms
- Deprecate basic logging in favor of comprehensive metrics

### Version 0.4.0 (Planned)
- Deprecate simple override decisions in favor of multi-pass validation
- Deprecate basic cost tracking in favor of cost-aware execution
- Deprecate generic prompts in favor of context-aware prompts

---

## Breaking Changes

### Version 0.2.0
- Configuration file structure changed significantly
- Threshold management system introduced
- Conditional execution logic added

### Version 0.1.0
- Evaluation pipeline architecture changed
- New evaluation modes introduced
- Configuration format updated

---

## Contributors

### Version 0.2.0
- **David Proctor**: Threshold optimization system design and implementation
- **Research Team**: Phase 4 feature planning and documentation

### Version 0.1.0
- **David Proctor**: Core hybrid architecture and evaluation system
- **Open Source Community**: Dataset support and model integration

### Version 0.0.1
- **David Proctor**: Initial project setup and structure

---

## Acknowledgments

- **GEPA Research Team**: Guided Editing and Prompt Analysis methodology
- **AGIEval Dataset**: Challenging educational evaluation benchmarks
- **OpenAI & Anthropic**: LLM providers and API support
- **Open Source Community**: Tools, libraries, and frameworks

---

*For detailed information about each release, see the [GitHub releases page](https://github.com/dp-pcs/gepa-tutor-refinery/releases).*
