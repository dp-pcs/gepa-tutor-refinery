#!/usr/bin/env python3
"""
Simple demonstration of the threshold system
"""

import yaml
import pathlib

def demo_config_loading():
    """Demonstrate configuration loading"""
    print("🔧 Loading Threshold Configuration")
    print("=" * 50)
    
    config_path = "configs/threshold_experiments.yaml"
    if not pathlib.Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ Configuration loaded: {config['experiment_name']}")
    
    # Show threshold configuration
    print(f"\n📊 Threshold Configuration:")
    print(f"   Default thresholds: {config['thresholds']['confidence_levels']}")
    
    dataset_thresholds = config['thresholds'].get('dataset_specific', {})
    if dataset_thresholds:
        print(f"   Dataset-specific thresholds:")
        for dataset, thresholds in dataset_thresholds.items():
            print(f"     {dataset}: {thresholds}")
    
    # Show conditional GEPA settings
    conditional_settings = config['conditional_gepa']
    print(f"\n🔄 Conditional GEPA Settings:")
    print(f"   Enabled: {conditional_settings['enabled']}")
    print(f"   Uncertainty signals: {len(conditional_settings['uncertainty_signals'])}")
    print(f"   Length thresholds: {conditional_settings['length_thresholds']}")
    print(f"   Reasoning indicators: {len(conditional_settings['reasoning_indicators'])}")
    
    # Show explicit invalidation settings
    invalidation_settings = config['explicit_invalidation']
    print(f"\n✅ Explicit Invalidation Settings:")
    print(f"   Required: {invalidation_settings['required']}")
    print(f"   Keywords: {len(invalidation_settings['keywords'])}")
    
    return True

def demo_threshold_logic():
    """Demonstrate threshold decision logic"""
    print(f"\n🧮 Threshold Decision Logic")
    print("=" * 50)
    
    # Simulate different confidence scenarios
    scenarios = [
        (0.75, "Low confidence - below typical threshold"),
        (0.80, "Medium confidence - at typical threshold"),
        (0.85, "High confidence - above typical threshold"),
        (0.90, "Very high confidence - conservative threshold"),
        (0.95, "Extreme confidence - ultra-conservative threshold")
    ]
    
    for confidence, description in scenarios:
        if confidence >= 0.85:
            decision = "GEPA OVERRIDE (if explicit invalidation)"
        elif confidence >= 0.80:
            decision = "GEPA OVERRIDE (standard threshold)"
        else:
            decision = "Use SR answer (below threshold)"
        
        print(f"   Confidence {confidence:.2f}: {decision}")
        print(f"     {description}")
    
    print(f"\n💡 Key Insights:")
    print(f"   - Thresholds ≥ 0.85 require explicit invalidation")
    print(f"   - Thresholds ≥ 0.80 allow standard overrides")
    print(f"   - Thresholds < 0.80 stick with SR answers")

def demo_conditional_execution():
    """Demonstrate conditional GEPA execution"""
    print(f"\n🎯 Conditional GEPA Execution")
    print("=" * 50)
    
    # Example SR outputs that would trigger different behaviors
    examples = [
        ("The answer is clearly A because the evidence shows...", "GEPA EXECUTES (confident, well-reasoned)"),
        ("I think the answer might be B...", "GEPA SKIPPED (uncertainty signal: 'I think', 'might')"),
        ("The answer is A.", "GEPA SKIPPED (too short, no reasoning)"),
        ("Based on the passage, the answer is C since the author argues...", "GEPA EXECUTES (well-reasoned)"),
        ("It seems like the answer could be D...", "GEPA SKIPPED (uncertainty signal: 'seems like', 'could')")
    ]
    
    for sr_output, decision in examples:
        print(f"   SR Output: '{sr_output}'")
        print(f"   Decision: {decision}")
        print()

def main():
    """Main demonstration function"""
    print("🚀 Threshold System Demonstration")
    print("=" * 60)
    
    # Load and display configuration
    if not demo_config_loading():
        return
    
    # Demonstrate threshold logic
    demo_threshold_logic()
    
    # Demonstrate conditional execution
    demo_conditional_execution()
    
    print("🎉 Demonstration completed!")
    print("\n📚 Next steps:")
    print("   1. Run: python3 scripts/run_threshold_experiments.py")
    print("   2. Run: python3 scripts/run_multi_dataset_threshold_experiments.py")
    print("   3. Check generated reports in the 'report/' directory")

if __name__ == "__main__":
    main()
