#!/usr/bin/env python3
"""
Threshold Experiment Script for Hybrid SR → GEPA
Runs experiments with different confidence thresholds and conditional execution
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

def run_threshold_experiment(config: Dict[str, Any], threshold: float, dataset_name: str) -> Dict[str, Any]:
    """Run a single threshold experiment"""
    print(f"\n🔬 Running threshold experiment: {threshold:.2f}")
    
    # Create a temporary config with this threshold
    temp_config = config.copy()
    temp_config['thresholds']['current_threshold'] = threshold
    
    # Save temporary config
    temp_config_path = f"configs/temp_threshold_{threshold:.2f}.yaml"
    with open(temp_config_path, 'w') as f:
        yaml.dump(temp_config, f, default_flow_style=False)
    
    try:
        # Run hybrid evaluation with this threshold
        eval_cmd = f"python -m src.run_loop --config {temp_config_path} --mode hybrid"
        success, output = run_command(eval_cmd, f"Hybrid evaluation with threshold {threshold:.2f}")
        
        if success:
            # Extract results from the run
            # Find the most recent run directory
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

def run_threshold_sweep(config: Dict[str, Any], dataset_name: str) -> List[Dict[str, Any]]:
    """Run experiments across all thresholds for a dataset"""
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
    
    # Update config with current dataset
    config['dataset']['name'] = dataset_name
    
    # Run experiments for each threshold
    results = []
    for threshold in thresholds:
        result = run_threshold_experiment(config, threshold, dataset_name)
        results.append(result)
        
        if result['success']:
            print(f"✅ Threshold {threshold:.2f}: Dev={result['dev_accuracy']:.3f}, Test={result['test_accuracy']:.3f}")
            print(f"   Overrides: {result['override_stats']['overrides']}, Success Rate: {result['override_stats']['override_success_rate']:.3f}")
        else:
            print(f"❌ Threshold {threshold:.2f}: Failed - {result.get('error', 'Unknown error')}")
    
    return results

def generate_threshold_report(results: List[Dict[str, Any]], dataset_name: str, config: Dict[str, Any]) -> str:
    """Generate a comprehensive report for threshold experiments"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"report/{dataset_name}_threshold_experiments_{timestamp}.md"
    
    # Create report directory if it doesn't exist
    pathlib.Path("report").mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(f"# Threshold Experiment Results: {dataset_name.upper()}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Dataset:** {dataset_name}\n")
        f.write(f"**Model:** {config['model']['model_id']}\n\n")
        
        f.write("## Configuration\n\n")
        f.write(f"- **Conditional GEPA:** {'Enabled' if config['conditional_gepa']['enabled'] else 'Disabled'}\n")
        f.write(f"- **Explicit Invalidation Required:** {'Yes' if config['explicit_invalidation']['required'] else 'No'}\n")
        f.write(f"- **Dev Set Size:** {config['dataset']['n_dev']}\n")
        f.write(f"- **Test Set Size:** {config['dataset']['n_test']}\n\n")
        
        f.write("## Results Summary\n\n")
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
        
        f.write("\n## Key Insights\n\n")
        
        # Find best performing threshold
        successful_results = [r for r in results if r['success']]
        if successful_results:
            best_result = max(successful_results, key=lambda x: x['test_accuracy'])
            f.write(f"- **Best Threshold:** {best_result['threshold']:.2f} (Test Acc: {best_result['test_accuracy']:.3f})\n")
            
            # Calculate cost per correct answer
            if best_result['test_avg_tokens_out'] > 0:
                cost_per_correct = best_result['test_avg_tokens_out'] / best_result['test_accuracy']
                f.write(f"- **Cost per Correct Answer:** {cost_per_correct:.1f} tokens\n")
            
            f.write(f"- **Override Success Rate:** {best_result['override_stats']['override_success_rate']:.3f}\n")
            f.write(f"- **GEPA Skip Rate:** {best_result['override_stats']['gepa_skip_rate']:.3f}\n")
        
        f.write("\n## Recommendations\n\n")
        
        # Analyze threshold trends
        if len(successful_results) >= 2:
            accuracies = [(r['threshold'], r['test_accuracy']) for r in successful_results]
            accuracies.sort()
            
            if accuracies[-1][1] > accuracies[0][1]:
                f.write("- **Threshold Impact:** Higher thresholds appear to improve accuracy\n")
            elif accuracies[-1][1] < accuracies[0][1]:
                f.write("- **Threshold Impact:** Lower thresholds appear to improve accuracy\n")
            else:
                f.write("- **Threshold Impact:** Threshold changes have minimal impact on accuracy\n")
        
        f.write("\n## Next Steps\n\n")
        f.write("1. **Fine-tune the sweet spot:** Run additional experiments around the best performing threshold\n")
        f.write("2. **Test on other datasets:** Apply the optimal threshold to other datasets\n")
        f.write("3. **Conditional execution tuning:** Adjust uncertainty signals and length thresholds\n")
        f.write("4. **Cost optimization:** Balance accuracy improvements with token cost increases\n")
    
    return report_path

def main():
    """Main function to run threshold experiments"""
    print("🚀 Starting Threshold Experiments for Hybrid SR → GEPA")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    config_path = "configs/threshold_experiments.yaml"
    if not pathlib.Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return
    
    config = load_config(config_path)
    print(f"✅ Loaded configuration: {config['experiment_name']}")
    
    # Get dataset name from config
    dataset_name = config['dataset']['name']
    print(f"📚 Target dataset: {dataset_name}")
    
    # Run threshold sweep
    results = run_threshold_sweep(config, dataset_name)
    
    if results:
        # Generate report
        report_path = generate_threshold_report(results, dataset_name, config)
        print(f"\n📊 Report generated: {report_path}")
        
        # Print summary
        print(f"\n{'#'*80}")
        print("📋 THRESHOLD EXPERIMENT SUMMARY")
        print(f"{'#'*80}")
        
        successful_results = [r for r in results if r['success']]
        if successful_results:
            best_result = max(successful_results, key=lambda x: x['test_accuracy'])
            print(f"🏆 Best Threshold: {best_result['threshold']:.2f}")
            print(f"   Test Accuracy: {best_result['test_accuracy']:.3f}")
            print(f"   Override Success Rate: {best_result['override_stats']['override_success_rate']:.3f}")
            print(f"   GEPA Skip Rate: {best_result['override_stats']['gepa_skip_rate']:.3f}")
        else:
            print("❌ No successful experiments")
        
        print(f"\n🎉 Threshold experiments completed!")
        print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("❌ No results generated")

if __name__ == "__main__":
    main()
