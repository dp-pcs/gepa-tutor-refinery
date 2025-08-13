#!/usr/bin/env python3
"""
Multi-Dataset Threshold Experiment Script
Runs threshold experiments across multiple datasets to find optimal thresholds for each
"""

import subprocess
import time
import pathlib
import yaml
import json
from datetime import datetime
from typing import List, Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_command(cmd: str, description: str) -> tuple[bool, str]:
    """Run a command and handle errors gracefully"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        end_time = time.time()
        
        print(f"✅ SUCCESS: {description}")
        print(f"⏱️  Time: {end_time - start_time:.2f}s")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {description}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        
        return False, e.stderr

def setup_data_for_dataset(dataset_name: str, n_dev: int, n_test: int) -> bool:
    """Setup data for a specific dataset"""
    setup_cmd = f"python scripts/setup_data.py --dataset {dataset_name} --n_train 0 --n_dev {n_dev} --n_test {n_test}"
    success, _ = run_command(setup_cmd, f"Setup data for {dataset_name}")
    return success

def run_single_threshold_experiment(config: Dict[str, Any], threshold: float, dataset_name: str) -> Dict[str, Any]:
    """Run a single threshold experiment for a specific dataset"""
    print(f"\n🔬 Running threshold experiment: {threshold:.2f} for {dataset_name}")
    
    # Create a temporary config with this threshold and dataset
    temp_config = config.copy()
    temp_config['thresholds']['current_threshold'] = threshold
    temp_config['dataset']['name'] = dataset_name
    
    # Save temporary config
    temp_config_path = f"configs/temp_{dataset_name}_threshold_{threshold:.2f}.yaml"
    with open(temp_config_path, 'w') as f:
        yaml.dump(temp_config, f, default_flow_style=False)
    
    try:
        # Run hybrid evaluation with this threshold
        eval_cmd = f"python -m src.run_loop --config {temp_config_path} --mode hybrid"
        success, output = run_command(eval_cmd, f"Hybrid evaluation with threshold {threshold:.2f} for {dataset_name}")
        
        if success:
            # Extract results from the run
            runs_dir = pathlib.Path(config['logging']['runs_dir'])
            run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and 'hybrid' in d.name]
            if run_dirs:
                latest_run = max(run_dirs, key=lambda x: x.stat().st_mtime)
                
                # Load summary
                summary_path = latest_run / "summary.json"
                if summary_path.exists():
                    with open(summary_path, 'r') as f:
                        summary = json.load(f)
                    
                    # Load detailed records for analysis
                    dev_records_path = latest_run / "dev" / "records.jsonl"
                    test_records_path = latest_run / "test" / "records.jsonl"
                    
                    dev_records = []
                    test_records = []
                    
                    if dev_records_path.exists():
                        with open(dev_records_path, 'r') as f:
                            dev_records = [json.loads(line) for line in f]
                    
                    if test_records_path.exists():
                        with open(test_records_path, 'r') as f:
                            test_records = [json.loads(line) for line in f]
                    
                    # Calculate override statistics
                    override_stats = calculate_override_stats(dev_records + test_records)
                    
                    return {
                        "dataset": dataset_name,
                        "threshold": threshold,
                        "success": True,
                        "dev_accuracy": summary.get("dev_accuracy", 0.0),
                        "test_accuracy": summary.get("test_accuracy", 0.0),
                        "dev_avg_tokens_out": summary.get("dev_avg_tokens_out", 0.0),
                        "test_avg_tokens_out": summary.get("test_avg_tokens_out", 0.0),
                        "override_stats": override_stats,
                        "run_dir": str(latest_run)
                    }
        
        return {
            "dataset": dataset_name,
            "threshold": threshold,
            "success": False,
            "error": output
        }
        
    finally:
        # Clean up temporary config
        pathlib.Path(temp_config_path).unlink(missing_ok=True)

def calculate_override_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics about GEPA overrides"""
    total_examples = len(records)
    overrides = 0
    successful_overrides = 0
    skipped_gepa = 0
    
    for record in records:
        if record.get("strategy") == "hybrid":
            usage = record.get("usage", {})
            if "gepa_confidence" in usage:
                # This was a hybrid run with confidence tracking
                if usage.get("gepa_confidence", 0) > 0:
                    overrides += 1
                    if record.get("correct") == 1:
                        successful_overrides += 1
                else:
                    skipped_gepa += 1
    
    return {
        "total_examples": total_examples,
        "overrides": overrides,
        "successful_overrides": successful_overrides,
        "skipped_gepa": skipped_gepa,
        "override_success_rate": successful_overrides / overrides if overrides > 0 else 0.0,
        "gepa_skip_rate": skipped_gepa / total_examples if total_examples > 0 else 0.0
    }

def run_dataset_threshold_sweep(config: Dict[str, Any], dataset_name: str) -> List[Dict[str, Any]]:
    """Run threshold sweep for a specific dataset"""
    print(f"\n{'#'*80}")
    print(f"🔬 THRESHOLD SWEEP FOR {dataset_name.upper()}")
    print(f"{'#'*80}")
    
    # Get thresholds for this dataset
    if dataset_name in config['thresholds'].get('dataset_specific', {}):
        thresholds = config['thresholds']['dataset_specific'][dataset_name]
        print(f"📊 Using dataset-specific thresholds: {thresholds}")
    else:
        thresholds = config['thresholds']['confidence_levels']
        print(f"📊 Using default thresholds: {thresholds}")
    
    # Setup data
    n_dev = config['dataset']['n_dev']
    n_test = config['dataset']['n_test']
    
    if not setup_data_for_dataset(dataset_name, n_dev, n_test):
        print(f"❌ Failed to setup data for {dataset_name}")
        return []
    
    # Run experiments for each threshold
    results = []
    for threshold in thresholds:
        result = run_single_threshold_experiment(config, threshold, dataset_name)
        results.append(result)
        
        if result['success']:
            print(f"✅ Threshold {threshold:.2f}: Dev={result['dev_accuracy']:.3f}, Test={result['test_accuracy']:.3f}")
            print(f"   Overrides: {result['override_stats']['overrides']}, Success Rate: {result['override_stats']['override_success_rate']:.3f}")
        else:
            print(f"❌ Threshold {threshold:.2f}: Failed - {result.get('error', 'Unknown error')}")
    
    return results

def generate_comprehensive_report(all_results: Dict[str, List[Dict[str, Any]]], config: Dict[str, Any]) -> str:
    """Generate a comprehensive report for all datasets and thresholds"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"report/comprehensive_threshold_experiments_{timestamp}.md"
    
    # Create report directory if it doesn't exist
    pathlib.Path("report").mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(f"# Comprehensive Threshold Experiment Results\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model:** {config['model']['model_id']}\n")
        f.write(f"**Total Datasets:** {len(all_results)}\n\n")
        
        f.write("## Configuration\n\n")
        f.write(f"- **Conditional GEPA:** {'Enabled' if config['conditional_gepa']['enabled'] else 'Disabled'}\n")
        f.write(f"- **Explicit Invalidation Required:** {'Yes' if config['explicit_invalidation']['required'] else 'No'}\n")
        f.write(f"- **Dev Set Size:** {config['dataset']['n_dev']}\n")
        f.write(f"- **Test Set Size:** {config['dataset']['n_test']}\n\n")
        
        # Dataset-specific results
        for dataset_name, results in all_results.items():
            f.write(f"## {dataset_name.upper()}\n\n")
            
            # Results table
            f.write("| Threshold | Dev Acc | Test Acc | Dev Tokens | Test Tokens | Overrides | Success Rate | GEPA Skips |\n")
            f.write("|-----------|---------|----------|------------|-------------|-----------|--------------|------------|\n")
            
            for result in results:
                if result['success']:
                    f.write(f"| {result['threshold']:.2f} | {result['dev_accuracy']:.3f} | {result['test_accuracy']:.3f} | ")
                    f.write(f"{result['dev_avg_tokens_out']:.1f} | {result['test_avg_tokens_out']:.1f} | ")
                    f.write(f"{result['override_stats']['overrides']} | {result['override_stats']['override_success_rate']:.3f} | ")
                    f.write(f"{result['override_stats']['gepa_skip_rate']:.3f} |\n")
                else:
                    f.write(f"| {result['threshold']:.2f} | FAILED | FAILED | FAILED | FAILED | FAILED | FAILED | FAILED |\n")
            
            # Find best performing threshold for this dataset
            successful_results = [r for r in results if r['success']]
            if successful_results:
                best_result = max(successful_results, key=lambda x: x['test_accuracy'])
                f.write(f"\n**Best Threshold:** {best_result['threshold']:.2f} (Test Acc: {best_result['test_accuracy']:.3f})\n")
                
                # Calculate cost per correct answer
                if best_result['test_avg_tokens_out'] > 0:
                    cost_per_correct = best_result['test_avg_tokens_out'] / best_result['test_accuracy']
                    f.write(f"**Cost per Correct Answer:** {cost_per_correct:.1f} tokens\n")
                
                f.write(f"**Override Success Rate:** {best_result['override_stats']['override_success_rate']:.3f}\n")
                f.write(f"**GEPA Skip Rate:** {best_result['override_stats']['gepa_skip_rate']:.3f}\n")
            
            f.write("\n---\n\n")
        
        # Overall insights
        f.write("## Overall Insights\n\n")
        
        # Find best thresholds across all datasets
        best_thresholds = {}
        for dataset_name, results in all_results.items():
            successful_results = [r for r in results if r['success']]
            if successful_results:
                best_result = max(successful_results, key=lambda x: x['test_accuracy'])
                best_thresholds[dataset_name] = {
                    'threshold': best_result['threshold'],
                    'accuracy': best_result['test_accuracy'],
                    'cost_per_correct': best_result['test_avg_tokens_out'] / best_result['test_accuracy'] if best_result['test_avg_tokens_out'] > 0 else 0
                }
        
        if best_thresholds:
            f.write("### Optimal Thresholds by Dataset\n\n")
            f.write("| Dataset | Optimal Threshold | Test Accuracy | Cost per Correct |\n")
            f.write("|---------|-------------------|---------------|------------------|\n")
            
            for dataset_name, stats in best_thresholds.items():
                f.write(f"| {dataset_name} | {stats['threshold']:.2f} | {stats['accuracy']:.3f} | {stats['cost_per_correct']:.1f} |\n")
        
        f.write("\n## Recommendations\n\n")
        
        # Analyze patterns
        if len(best_thresholds) >= 2:
            # Check if there are clear patterns
            thresholds = [stats['threshold'] for stats in best_thresholds.values()]
            avg_threshold = sum(thresholds) / len(thresholds)
            
            f.write(f"- **Average Optimal Threshold:** {avg_threshold:.2f}\n")
            
            # Identify most challenging datasets
            challenging_datasets = [name for name, stats in best_thresholds.items() if stats['threshold'] >= 0.90]
            if challenging_datasets:
                f.write(f"- **Most Challenging Datasets:** {', '.join(challenging_datasets)} (require thresholds ≥ 0.90)\n")
            
            # Identify easier datasets
            easier_datasets = [name for name, stats in best_thresholds.items() if stats['threshold'] <= 0.80]
            if easier_datasets:
                f.write(f"- **Easier Datasets:** {', '.join(easier_datasets)} (can use thresholds ≤ 0.80)\n")
        
        f.write("\n## Next Steps\n\n")
        f.write("1. **Apply optimal thresholds:** Use the dataset-specific thresholds found in this experiment\n")
        f.write("2. **Fine-tune around sweet spots:** Run additional experiments around the best thresholds\n")
        f.write("3. **Cross-dataset validation:** Test if optimal thresholds generalize across similar datasets\n")
        f.write("4. **Production deployment:** Implement the optimal threshold configuration in production\n")
    
    return report_path

def main():
    """Main function to run threshold experiments across multiple datasets"""
    print("🚀 Starting Multi-Dataset Threshold Experiments for Hybrid SR → GEPA")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    config_path = "configs/threshold_experiments.yaml"
    if not pathlib.Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return
    
    config = load_config(config_path)
    print(f"✅ Loaded configuration: {config['experiment_name']}")
    
    # Get all datasets to test
    dataset_thresholds = config['thresholds'].get('dataset_specific', {})
    if not dataset_thresholds:
        print("❌ No dataset-specific thresholds configured")
        return
    
    datasets_to_test = list(dataset_thresholds.keys())
    print(f"📚 Testing {len(datasets_to_test)} datasets: {', '.join(datasets_to_test)}")
    
    # Run experiments for each dataset
    all_results = {}
    for dataset_name in datasets_to_test:
        print(f"\n{'='*80}")
        print(f"🎯 PROCESSING DATASET: {dataset_name.upper()}")
        print(f"{'='*80}")
        
        results = run_dataset_threshold_sweep(config, dataset_name)
        if results:
            all_results[dataset_name] = results
            print(f"✅ Completed threshold sweep for {dataset_name}")
        else:
            print(f"❌ Failed threshold sweep for {dataset_name}")
    
    if all_results:
        # Generate comprehensive report
        report_path = generate_comprehensive_report(all_results, config)
        print(f"\n📊 Comprehensive report generated: {report_path}")
        
        # Print summary
        print(f"\n{'#'*80}")
        print("📋 COMPREHENSIVE THRESHOLD EXPERIMENT SUMMARY")
        print(f"{'#'*80}")
        
        for dataset_name, results in all_results.items():
            successful_results = [r for r in results if r['success']]
            if successful_results:
                best_result = max(successful_results, key=lambda x: x['test_accuracy'])
                print(f"\n🏆 {dataset_name.upper()}:")
                print(f"   Best Threshold: {best_result['threshold']:.2f}")
                print(f"   Test Accuracy: {best_result['test_accuracy']:.3f}")
                print(f"   Override Success Rate: {best_result['override_stats']['override_success_rate']:.3f}")
                print(f"   GEPA Skip Rate: {best_result['override_stats']['gepa_skip_rate']:.3f}")
            else:
                print(f"\n❌ {dataset_name.upper()}: No successful experiments")
        
        print(f"\n🎉 Multi-dataset threshold experiments completed!")
        print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("❌ No results generated for any dataset")

if __name__ == "__main__":
    main()
