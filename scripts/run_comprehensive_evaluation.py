#!/usr/bin/env python3
"""
Comprehensive Evaluation Script for All 6 Datasets
Runs baseline, self-refine, and GEPA modes across all datasets
"""

import subprocess
import time
import pathlib
from datetime import datetime

# Configuration for each dataset
DATASETS = [
    {
        "name": "gpqa_diamond",
        "n_train": 0,
        "n_dev": 50,
        "n_test": 50,
        "description": "GPQA-Diamond (extremely challenging STEM)"
    },
    {
        "name": "mmlu_pro", 
        "n_train": 0,
        "n_dev": 50,
        "n_test": 50,
        "description": "MMLU-Pro (10-choice questions)"
    },
    {
        "name": "agieval_lsat_ar",
        "n_train": 0,
        "n_dev": 50,
        "n_test": 50,
        "description": "AGIEval LSAT-AR (analytical reasoning)"
    },
    {
        "name": "agieval_lsat_lr",
        "n_train": 0,
        "n_dev": 50,
        "n_test": 50,
        "description": "AGIEval LSAT-LR (logical reasoning)"
    },
    {
        "name": "agieval_sat_math",
        "n_train": 0,
        "n_dev": 50,
        "n_test": 50,
        "description": "AGIEval SAT-Math (mathematical reasoning)"
    },
    {
        "name": "logiqa2",
        "n_train": 0,
        "n_dev": 50,
        "n_test": 50,
        "description": "LogiQA 2.0 (massive logical reasoning)"
    },
    {
        "name": "truthfulqa_official",
        "n_train": 0,
        "n_dev": 50,
        "n_test": 50,
        "description": "TruthfulQA (adversarial truthfulness)"
    }
]

MODES = ["baseline", "self_refine", "gepa"]

def run_command(cmd, description):
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

def main():
    """Run comprehensive evaluation across all datasets"""
    print("🚀 Starting Comprehensive Evaluation Across All 6 Datasets")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Total datasets: {len(DATASETS)}")
    print(f"🔧 Total modes: {len(MODES)}")
    print(f"📊 Total evaluations: {len(DATASETS) * len(MODES)}")
    
    results = {}
    
    for dataset in DATASETS:
        dataset_name = dataset["name"]
        print(f"\n{'#'*80}")
        print(f"📚 Processing Dataset: {dataset_name}")
        print(f"📝 Description: {dataset['description']}")
        print(f"{'#'*80}")
        
        results[dataset_name] = {}
        
        # Step 1: Setup data
        setup_cmd = f"python scripts/setup_data.py --dataset {dataset_name} --n_train {dataset['n_train']} --n_dev {dataset['n_dev']} --n_test {dataset['n_test']}"
        success, output = run_command(setup_cmd, f"Setup data for {dataset_name}")
        
        if not success:
            print(f"⚠️  Skipping {dataset_name} due to setup failure")
            continue
        
        # Step 2: Run all modes
        for mode in MODES:
            print(f"\n🔄 Running {mode.upper()} mode for {dataset_name}")
            
            # Update config to use the dataset
            config_update_cmd = f"sed -i '' 's/name: .*/name: {dataset_name}/' configs/config.yaml"
            run_command(config_update_cmd, f"Update config for {dataset_name}")
            
            # Run evaluation
            eval_cmd = f"python -m src.run_loop --config configs/config.yaml --mode {mode}"
            success, output = run_command(eval_cmd, f"{mode.upper()} evaluation for {dataset_name}")
            
            if success:
                results[dataset_name][mode] = "SUCCESS"
                print(f"✅ {mode.upper()} completed for {dataset_name}")
            else:
                results[dataset_name][mode] = "FAILED"
                print(f"❌ {mode.upper()} failed for {dataset_name}")
        
        # Step 3: Generate report for this dataset
        report_cmd = f"python scripts/make_report.py --runs_dir runs --out report/{dataset_name}_results.md"
        run_command(report_cmd, f"Generate report for {dataset_name}")
    
    # Step 4: Generate comprehensive report
    print(f"\n{'#'*80}")
    print("📊 Generating Comprehensive Report")
    print(f"{'#'*80}")
    
    comprehensive_report_cmd = "python scripts/make_report.py --runs_dir runs --out report/comprehensive_evaluation.md"
    run_command(comprehensive_report_cmd, "Generate comprehensive evaluation report")
    
    # Step 5: Print summary
    print(f"\n{'#'*80}")
    print("📋 EVALUATION SUMMARY")
    print(f"{'#'*80}")
    
    for dataset_name, modes in results.items():
        print(f"\n📚 {dataset_name.upper()}:")
        for mode, status in modes.items():
            print(f"  {mode:12}: {status}")
    
    print(f"\n🎉 Comprehensive evaluation completed!")
    print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
