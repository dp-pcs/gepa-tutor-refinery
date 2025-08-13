#!/usr/bin/env python3
"""
Test script for a single dataset to verify the pipeline works
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and handle errors gracefully"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ SUCCESS: {description}")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {description}")
        print(f"Exit code: {e.returncode}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def main():
    """Test a single dataset end-to-end"""
    dataset = "gpqa_diamond"
    
    print(f"🧪 Testing Dataset: {dataset}")
    print("This will test the complete pipeline: setup → baseline → self_refine → gepa → report")
    
    # Step 1: Setup data
    if not run_command(f"python scripts/setup_data.py --dataset {dataset} --n_train 0 --n_dev 20 --n_test 20", 
                      f"Setup data for {dataset}"):
        print("❌ Setup failed, aborting")
        sys.exit(1)
    
    # Step 2: Update config
    if not run_command(f"sed -i '' 's/name: .*/name: {dataset}/' configs/config.yaml", 
                      f"Update config for {dataset}"):
        print("❌ Config update failed, aborting")
        sys.exit(1)
    
    # Step 3: Run baseline
    if not run_command("python -m src.run_loop --config configs/config.yaml --mode baseline", 
                      f"Baseline evaluation for {dataset}"):
        print("❌ Baseline failed, aborting")
        sys.exit(1)
    
    # Step 4: Run self_refine
    if not run_command("python -m src.run_loop --config configs/config.yaml --mode self_refine", 
                      f"Self-refine evaluation for {dataset}"):
        print("❌ Self-refine failed, aborting")
        sys.exit(1)
    
    # Step 5: Run GEPA
    if not run_command("python -m src.run_loop --config configs/config.yaml --mode gepa", 
                      f"GEPA evaluation for {dataset}"):
        print("❌ GEPA failed, aborting")
        sys.exit(1)
    
    # Step 6: Generate report
    if not run_command("python scripts/make_report.py --runs_dir runs --out report/test_results.md", 
                      f"Generate report for {dataset}"):
        print("❌ Report generation failed, aborting")
        sys.exit(1)
    
    print(f"\n🎉 SUCCESS: Complete pipeline test for {dataset} completed!")
    print("You can now run the comprehensive evaluation across all datasets.")

if __name__ == "__main__":
    main()
