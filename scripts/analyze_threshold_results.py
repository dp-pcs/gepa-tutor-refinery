#!/usr/bin/env python3
"""
Analyze threshold experiment results
"""

import json
import pathlib
from typing import Dict, List, Any

def analyze_run_results(run_dir: str) -> Dict[str, Any]:
    """Analyze results from a single threshold experiment run"""
    run_path = pathlib.Path(run_dir)
    
    # Load summary
    summary_path = run_path / "summary.json"
    if not summary_path.exists():
        return {"error": "Summary not found"}
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    # Load dev records
    dev_records_path = run_path / "dev" / "records.jsonl"
    test_records_path = run_path / "test" / "records.jsonl"
    
    dev_records = []
    test_records = []
    
    if dev_records_path.exists():
        with open(dev_records_path, 'r') as f:
            dev_records = [json.loads(line) for line in f]
    
    if test_records_path.exists():
        with open(test_records_path, 'r') as f:
            test_records = [json.loads(line) for line in f]
    
    # Calculate override statistics
    def calculate_override_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_examples = len(records)
        overrides = 0
        successful_overrides = 0
        skipped_gepa = 0
        confidence_scores = []
        
        for record in records:
            if record.get("strategy") == "hybrid":
                usage = record.get("usage", {})
                if "gepa_confidence" in usage:
                    confidence = usage.get("gepa_confidence", 0)
                    confidence_scores.append(confidence)
                    
                    if confidence > 0:
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
            "gepa_skip_rate": skipped_gepa / total_examples if total_examples > 0 else 0.0,
            "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "confidence_scores": confidence_scores
        }
    
    dev_stats = calculate_override_stats(dev_records)
    test_stats = calculate_override_stats(test_records)
    
    return {
        "summary": summary,
        "dev_stats": dev_stats,
        "test_stats": test_stats,
        "run_dir": str(run_path)
    }

def main():
    """Analyze all threshold experiment runs"""
    runs_dir = pathlib.Path("runs")
    
    # Find all hybrid runs
    hybrid_runs = [d for d in runs_dir.iterdir() if d.is_dir() and 'hybrid' in d.name]
    
    if not hybrid_runs:
        print("No hybrid runs found")
        return
    
    print(f"Found {len(hybrid_runs)} hybrid runs")
    
    # Analyze each run
    for run_dir in sorted(hybrid_runs, key=lambda x: x.stat().st_mtime):
        print(f"\n{'='*60}")
        print(f"Analyzing: {run_dir.name}")
        print(f"{'='*60}")
        
        results = analyze_run_results(str(run_dir))
        
        if "error" in results:
            print(f"Error: {results['error']}")
            continue
        
        summary = results["summary"]
        dev_stats = results["dev_stats"]
        test_stats = results["test_stats"]
        
        print(f"Mode: {summary['mode']}")
        print(f"Dev Accuracy: {summary['dev_accuracy']:.3f}")
        print(f"Test Accuracy: {summary['test_accuracy']:.3f}")
        print(f"Dev Tokens: {summary['dev_avg_tokens_out']:.1f}")
        print(f"Test Tokens: {summary['test_avg_tokens_out']:.1f}")
        
        print(f"\nDev Override Stats:")
        print(f"  Total Examples: {dev_stats['total_examples']}")
        print(f"  Overrides: {dev_stats['overrides']}")
        print(f"  Successful Overrides: {dev_stats['successful_overrides']}")
        print(f"  Override Success Rate: {dev_stats['override_success_rate']:.3f}")
        print(f"  GEPA Skips: {dev_stats['skipped_gepa']}")
        print(f"  GEPA Skip Rate: {dev_stats['gepa_skip_rate']:.3f}")
        print(f"  Average Confidence: {dev_stats['avg_confidence']:.3f}")
        
        print(f"\nTest Override Stats:")
        print(f"  Total Examples: {test_stats['total_examples']}")
        print(f"  Overrides: {test_stats['overrides']}")
        print(f"  Successful Overrides: {test_stats['successful_overrides']}")
        print(f"  Override Success Rate: {test_stats['override_success_rate']:.3f}")
        print(f"  GEPA Skips: {test_stats['skipped_gepa']}")
        print(f"  GEPA Skip Rate: {test_stats['gepa_skip_rate']:.3f}")
        print(f"  Average Confidence: {test_stats['avg_confidence']:.3f}")
        
        # Calculate cost per correct answer
        if summary['test_accuracy'] > 0:
            cost_per_correct = summary['test_avg_tokens_out'] / summary['test_accuracy']
            print(f"\nCost per Correct Answer: {cost_per_correct:.1f} tokens")

if __name__ == "__main__":
    main()
