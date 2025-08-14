# Contributing to Tutor Refinery

Thank you for your interest in contributing to Tutor Refinery! This document provides guidelines and information for contributors.

## 🎯 How to Contribute

We welcome contributions in many forms:

- **Bug reports** and **feature requests**
- **Code contributions** and **improvements**
- **Documentation** updates and enhancements
- **Testing** and **validation**
- **Research** and **experiments**
- **Community support** and **discussions**

## 🚀 Getting Started

### **Prerequisites**

- Python 3.10+
- Git
- Basic understanding of AI/ML concepts
- Familiarity with the project (read the main README first)

### **Setup Development Environment**

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/gepa-tutor-refinery.git
cd gepa-tutor-refinery

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Set up pre-commit hooks (if available)
pre-commit install
```

## 📋 Contribution Areas

### **High Priority Areas**

#### **Phase 4 Feature Implementation**
- **Context-Aware GEPA**: Domain-specific auditor prompts
- **Override Reason Logging**: Enhanced decision tracking
- **Multi-Pass Validation**: Second validation pass system
- **Weighted Confidence Scoring**: Dynamic threshold algorithms
- **Cost-Aware Execution**: Smart execution strategy selection

#### **Performance Optimization**
- **Threshold Algorithm Improvements**: Better confidence scoring
- **Cost Optimization**: Reduce token usage while maintaining accuracy
- **Latency Improvements**: Faster execution without quality loss

#### **Dataset Support**
- **New Educational Datasets**: Add support for additional domains
- **Dataset-Specific Prompts**: Optimize prompts for different subjects
- **Evaluation Metrics**: Domain-appropriate performance measures

### **Medium Priority Areas**

#### **Testing & Validation**
- **Unit Tests**: Comprehensive test coverage
- **Integration Tests**: End-to-end system validation
- **Performance Benchmarks**: Consistent evaluation metrics

#### **Documentation**
- **API Documentation**: Clear usage examples
- **Tutorials**: Step-by-step guides for common tasks
- **Research Papers**: Academic documentation of methods

#### **Tooling & Infrastructure**
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring Tools**: Performance tracking and alerting
- **Development Tools**: Code quality and formatting

### **Low Priority Areas**

#### **User Interface**
- **Web Dashboard**: Visual experiment management
- **CLI Improvements**: Better command-line experience
- **Configuration UI**: Visual configuration management

#### **Community & Outreach**
- **Workshop Materials**: Educational content
- **Conference Submissions**: Research presentations
- **Blog Posts**: Technical articles and insights

## 🔧 Development Workflow

### **1. Issue Creation**

Before starting work, create or find an issue:

- **Bug Report**: Describe the problem clearly
- **Feature Request**: Explain the proposed enhancement
- **Good First Issue**: Marked for new contributors
- **Help Wanted**: Areas needing assistance

### **2. Branch Strategy**

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Convention:**
- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/documentation-update` - Documentation changes
- `test/test-improvements` - Testing enhancements
- `refactor/code-improvements` - Code refactoring

### **3. Development Process**

```bash
# Make your changes
# ... edit files ...

# Add and commit changes
git add .
git commit -m "feat: implement context-aware GEPA prompts

- Add domain-specific prompt templates
- Implement prompt selection logic
- Add configuration options for different datasets
- Update evaluator to use domain-specific prompts"

# Push to your fork
git push origin feature/your-feature-name
```

**Commit Message Convention:**
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

### **4. Pull Request Process**

1. **Create PR** from your branch to main
2. **Fill PR Template** completely
3. **Link Issues** that the PR addresses
4. **Request Review** from maintainers
5. **Address Feedback** and make requested changes
6. **Wait for Approval** and merge

### **5. PR Template**

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test addition/update

## Related Issues
Closes #123
Addresses #456

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance benchmarks updated

## Documentation
- [ ] Code comments added/updated
- [ ] README updated if needed
- [ ] API documentation updated

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] All tests pass locally
- [ ] No breaking changes introduced
```

## 📝 Code Standards

### **Python Style Guide**

- Follow **PEP 8** style guidelines
- Use **type hints** for function parameters and return values
- Keep functions **small and focused** (max ~50 lines)
- Use **descriptive variable names**
- Add **docstrings** for all public functions and classes

### **Example Code Style**

```python
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ThresholdManager:
    """Manages confidence thresholds for GEPA override decisions."""
    
    def __init__(self, base_threshold: float = 0.85):
        """Initialize threshold manager.
        
        Args:
            base_threshold: Default confidence threshold for overrides
        """
        self.base_threshold = base_threshold
        self.dataset_thresholds: Dict[str, float] = {}
    
    def get_threshold(self, dataset_name: str) -> float:
        """Get threshold for specific dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Confidence threshold for the dataset
        """
        return self.dataset_thresholds.get(dataset_name, self.base_threshold)
    
    def set_dataset_threshold(self, dataset_name: str, threshold: float) -> None:
        """Set threshold for specific dataset.
        
        Args:
            dataset_name: Name of the dataset
            threshold: Confidence threshold value
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
        
        self.dataset_thresholds[dataset_name] = threshold
        logger.info(f"Set threshold for {dataset_name} to {threshold}")
```

### **Configuration Standards**

- Use **YAML** for configuration files
- Provide **default values** for all settings
- Include **comments** explaining configuration options
- Use **consistent naming** conventions

### **Documentation Standards**

- Write **clear and concise** descriptions
- Include **examples** for complex concepts
- Use **consistent formatting** and structure
- Keep **up-to-date** with code changes

## 🧪 Testing Guidelines

### **Test Coverage Requirements**

- **Minimum 80%** code coverage
- **Unit tests** for all public functions
- **Integration tests** for critical workflows
- **Performance tests** for optimization features

### **Test Structure**

```python
import pytest
from unittest.mock import Mock, patch
from src.threshold_manager import ThresholdManager


class TestThresholdManager:
    """Test cases for ThresholdManager class."""
    
    def test_init_with_default_threshold(self):
        """Test initialization with default threshold."""
        manager = ThresholdManager()
        assert manager.base_threshold == 0.85
    
    def test_get_threshold_for_unknown_dataset(self):
        """Test getting threshold for unknown dataset returns base."""
        manager = ThresholdManager(base_threshold=0.90)
        threshold = manager.get_threshold("unknown_dataset")
        assert threshold == 0.90
    
    def test_set_dataset_threshold_valid_value(self):
        """Test setting valid dataset threshold."""
        manager = ThresholdManager()
        manager.set_dataset_threshold("lsat_lr", 0.95)
        assert manager.get_threshold("lsat_lr") == 0.95
    
    def test_set_dataset_threshold_invalid_value(self):
        """Test setting invalid threshold raises error."""
        manager = ThresholdManager()
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            manager.set_dataset_threshold("lsat_lr", 1.5)
```

## 📊 Performance Requirements

### **Accuracy Benchmarks**

- **Maintain or improve** existing accuracy scores
- **Document performance impact** of all changes
- **Run benchmarks** before and after changes
- **Compare against baseline** implementations

### **Cost Efficiency**

- **Monitor token usage** for all changes
- **Maintain cost per correct answer** ratios
- **Document optimization trade-offs**
- **Benchmark against alternative approaches**

## 🔍 Review Process

### **Code Review Checklist**

- [ ] **Functionality**: Does the code work as intended?
- [ ] **Performance**: Are there performance implications?
- [ ] **Security**: Are there security concerns?
- [ ] **Testing**: Are tests comprehensive and passing?
- [ ] **Documentation**: Is documentation updated?
- [ ] **Style**: Does code follow project standards?

### **Review Timeline**

- **Initial Review**: Within 2-3 business days
- **Follow-up Reviews**: Within 1-2 business days
- **Final Approval**: After all concerns addressed
- **Merge**: Within 24 hours of approval

## 🚨 Reporting Issues

### **Bug Report Template**

```markdown
## Bug Description
Clear description of what the bug is.

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., macOS 12.0]
- Python Version: [e.g., 3.10.0]
- Package Version: [e.g., 0.1.0]

## Additional Context
Any other context about the problem.
```

### **Feature Request Template**

```markdown
## Feature Description
Clear description of the requested feature.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How should this feature work?

## Alternative Solutions
Any alternative approaches considered?

## Additional Context
Any other context or examples.
```

## 📚 Resources

### **Project Documentation**

- **[Main README](README.md)**: Project overview and quick start
- **[Threshold Optimization Guide](docs/THRESHOLD_OPTIMIZATION_README.md)**: System architecture
- **[Phase 4 Implementation Guide](docs/PHASE_4_IMPLEMENTATION_GUIDE.md)**: Advanced features
- **[API Documentation](docs/API.md)**: Technical reference

### **External Resources**

- **[GEPA Paper](https://arxiv.org/abs/2303.12626)**: Research methodology
- **[AGIEval Dataset](https://github.com/microsoft/AGIEval)**: Evaluation dataset
- **[Python Type Hints](https://docs.python.org/3/library/typing.html)**: Type annotation guide
- **[PEP 8](https://www.python.org/dev/peps/pep-0008/)**: Python style guide

## 🤝 Community Guidelines

### **Code of Conduct**

- **Be respectful** and inclusive
- **Welcome newcomers** and help them learn
- **Provide constructive feedback**
- **Focus on the code**, not the person
- **Celebrate contributions** and improvements

### **Communication Channels**

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community chat
- **Pull Requests**: Code review and collaboration
- **Email**: Private or sensitive matters

## 🏆 Recognition

### **Contributor Recognition**

- **Contributors list** in README
- **Release notes** acknowledgment
- **Special thanks** for significant contributions
- **Community spotlight** for outstanding work

### **Types of Contributions**

- **Code Contributors**: Direct code contributions
- **Documentation Contributors**: Documentation improvements
- **Testing Contributors**: Test coverage and validation
- **Community Contributors**: Support and outreach
- **Research Contributors**: Novel approaches and insights

## 📞 Getting Help

### **Before Asking for Help**

1. **Read the documentation** thoroughly
2. **Search existing issues** for similar problems
3. **Try to reproduce** the issue locally
4. **Check the troubleshooting guide**
5. **Prepare a minimal example**

### **How to Ask for Help**

- **Be specific** about the problem
- **Include relevant code** and error messages
- **Describe what you've tried** already
- **Provide context** about your environment
- **Be patient** and respectful

## 🎉 Thank You!

Thank you for contributing to Tutor Refinery! Your contributions help advance AI-powered education and make the system better for everyone.

Whether you're fixing a typo, implementing a major feature, or just asking questions, every contribution matters and is appreciated.

---

**Happy coding! 🚀**
