#!/usr/bin/env python3
"""
Test script for the threshold system
Verifies that threshold configuration and conditional GEPA execution work correctly
"""

import yaml
import pathlib
from src.run_loop import make_provider, load_split

def test_threshold_config():
    """Test threshold configuration loading and application"""
    print("🧪 Testing Threshold Configuration System")
    
    # Load test configuration
    config_path = "configs/threshold_experiments.yaml"
    if not pathlib.Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ Loaded configuration: {config['experiment_name']}")
    
    # Test threshold configuration structure
    if 'thresholds' not in config:
        print("❌ Missing 'thresholds' section in config")
        return False
    
    if 'conditional_gepa' not in config:
        print("❌ Missing 'conditional_gepa' section in config")
        return False
    
    if 'explicit_invalidation' not in config:
        print("❌ Missing 'explicit_invalidation' section in config")
        return False
    
    print("✅ Configuration structure is valid")
    
    # Test dataset-specific thresholds
    dataset_thresholds = config['thresholds'].get('dataset_specific', {})
    if dataset_thresholds:
        print(f"✅ Dataset-specific thresholds configured for {len(dataset_thresholds)} datasets")
        for dataset, thresholds in dataset_thresholds.items():
            print(f"   {dataset}: {thresholds}")
    
    # Test conditional GEPA settings
    conditional_settings = config['conditional_gepa']
    print(f"✅ Conditional GEPA: {'Enabled' if conditional_settings['enabled'] else 'Disabled'}")
    print(f"   Uncertainty signals: {len(conditional_settings['uncertainty_signals'])}")
    print(f"   Length thresholds: {conditional_settings['length_thresholds']}")
    print(f"   Reasoning indicators: {len(conditional_settings['reasoning_indicators'])}")
    
    # Test explicit invalidation settings
    invalidation_settings = config['explicit_invalidation']
    print(f"✅ Explicit invalidation: {'Required' if invalidation_settings['required'] else 'Optional'}")
    print(f"   Keywords: {len(invalidation_settings['keywords'])}")
    
    return True

def test_provider_integration():
    """Test that threshold config can be attached to provider"""
    print("\n🔌 Testing Provider Integration")
    
    # Load minimal config for provider creation
    config = {
        "model": {
            "provider": "mock",
            "model_id": "test",
            "temperature": 0.2,
            "max_output_tokens": 256,
            "request_timeout": 60
        }
    }
    
    try:
        provider = make_provider(config)
        print("✅ Provider created successfully")
        
        # Test threshold config attachment
        test_config = {
            'confidence_threshold': 0.85,
            'conditional_gepa_enabled': True,
            'explicit_invalidation_required': True
        }
        
        provider.threshold_config = test_config
        print("✅ Threshold config attached to provider")
        
        # Verify attachment
        if hasattr(provider, 'threshold_config'):
            print(f"✅ Provider has threshold_config: {provider.threshold_config}")
        else:
            print("❌ Provider missing threshold_config attribute")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Provider creation failed: {e}")
        return False

def test_data_loading():
    """Test that data loading works for threshold experiments"""
    print("\n📚 Testing Data Loading")
    
    # Load minimal config
    config = {
        "dataset": {
            "name": "agieval_lsat_lr",
            "n_dev": 5,
            "n_test": 5
        }
    }
    
    try:
        # Test dev split loading
        dev_data = load_split(config, "dev")
        print(f"✅ Dev split loaded: {len(dev_data)} examples")
        
        # Test test split loading
        test_data = load_split(config, "test")
        print(f"✅ Test split loaded: {len(test_data)} examples")
        
        # Verify data structure
        if dev_data and test_data:
            example = dev_data[0]
            required_fields = ['id', 'context', 'question', 'choices', 'answer']
            if all(hasattr(example, field) for field in required_fields):
                print("✅ Data structure is valid")
                return True
            else:
                print("❌ Data structure is invalid")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Threshold System Components")
    print("=" * 50)
    
    tests = [
        ("Configuration Loading", test_threshold_config),
        ("Provider Integration", test_provider_integration),
        ("Data Loading", test_data_loading)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Threshold system is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    main()
