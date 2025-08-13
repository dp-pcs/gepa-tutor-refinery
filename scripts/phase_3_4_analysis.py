#!/usr/bin/env python3
"""
Phase 3.4 Analysis: Override Pattern Study and Threshold Optimization

This script analyzes hybrid mode runs to:
1. Study override success patterns
2. Optimize confidence thresholds
3. Implement cost per correct analysis
4. Refine scoring criteria
"""

import json
import pathlib
from collections import defaultdict

def load_hybrid_runs(runs_dir="runs"):
    """Load all hybrid mode runs for analysis"""
    runs = []
    runs_path = pathlib.Path(runs_dir)
    
    for run_dir in runs_path.iterdir():
        if run_dir.is_dir() and "hybrid" in run_dir.name:
            summary_file = run_dir / "summary.json"
            if summary_file.exists():
                with open(summary_file) as f:
                    summary = json.load(f)
                    summary["run_dir"] = str(run_dir)
                    summary["run_name"] = run_dir.name
                    runs.append(summary)
    
    return runs

def analyze_override_patterns(run_dir):
    """Analyze override patterns in a specific hybrid run"""
    dev_records = pathlib.Path(run_dir) / "dev" / "records.jsonl"
    test_records = pathlib.Path(run_dir) / "test" / "records.jsonl"
    
    patterns = {
        "dev": {"overrides": [], "fallbacks": [], "total": 0},
        "test": {"overrides": [], "fallbacks": [], "total": 0}
    }
    
    for split, file_path in [("dev", dev_records), ("test", test_records)]:
        if not file_path.exists():
            continue
            
        with open(file_path) as f:
            for line in f:
                record = json.loads(line)
                patterns[split]["total"] += 1
                
                # Check if this was an override or fallback
                usage = record.get("usage", {})
                sr_output = usage.get("sr_output", "")
                gepa_output = usage.get("gepa_output", "")
                
                # Simple heuristic: if GEPA output is different from SR, it was an override
                if sr_output and gepa_output:
                    sr_answer = extract_answer(sr_output)
                    gepa_answer = extract_answer(gepa_output)
                    
                    if sr_answer != gepa_answer and gepa_answer:
                        patterns[split]["overrides"].append({
                            "id": record["id"],
                            "sr_answer": sr_answer,
                            "gepa_answer": gepa_answer,
                            "correct": record["correct"],
                            "sr_output": sr_output[:100],
                            "gepa_output": gepa_output[:100]
                        })
                    else:
                        patterns[split]["fallbacks"].append({
                            "id": record["id"],
                            "answer": sr_answer,
                            "correct": record["correct"]
                        })
    
    return patterns

def extract_answer(text):
    """Extract answer letter from text"""
    import re
    match = re.search(r'Answer:\s*([A-Z])', text)
    return match.group(1) if match else None

def calculate_cost_metrics(patterns, summary):
    """Calculate cost per correct answer metrics"""
    metrics = {}
    
    for split in ["dev", "test"]:
        if patterns[split]["total"] == 0:
            continue
            
        total_correct = sum(1 for item in patterns[split]["overrides"] + patterns[split]["fallbacks"] 
                           if item["correct"])
        
        if total_correct > 0:
            # Get token usage from summary
            avg_tokens = summary.get(f"{split}_avg_tokens_out", 0)
            cost_per_correct = avg_tokens / total_correct if total_correct > 0 else float('inf')
            
            metrics[split] = {
                "total_correct": total_correct,
                "avg_tokens": avg_tokens,
                "cost_per_correct": cost_per_correct,
                "override_rate": len(patterns[split]["overrides"]) / patterns[split]["total"],
                "override_success_rate": sum(1 for item in patterns[split]["overrides"] 
                                           if item["correct"]) / max(len(patterns[split]["overrides"]), 1)
            }
    
    return metrics

def analyze_confidence_distribution(run_dir):
    """Analyze confidence score distribution from console output"""
    # This would require parsing console logs or adding confidence logging
    # For now, we'll analyze the patterns we can extract
    return {}

def generate_optimization_recommendations(patterns, metrics):
    """Generate recommendations for threshold optimization"""
    recommendations = []
    
    # Analyze override success rates
    for split in ["dev", "test"]:
        if split in metrics:
            override_rate = metrics[split]["override_rate"]
            success_rate = metrics[split]["override_success_rate"]
            
            if override_rate < 0.1:
                recommendations.append(f"Low override rate ({override_rate:.1%}) on {split} - consider lowering confidence threshold")
            elif success_rate < 0.5:
                recommendations.append(f"Low override success rate ({success_rate:.1%}) on {split} - consider raising confidence threshold")
            else:
                recommendations.append(f"Good override performance on {split}: {override_rate:.1%} rate, {success_rate:.1%} success")
    
    # Analyze cost efficiency
    for split in ["dev", "test"]:
        if split in metrics:
            cost_per_correct = metrics[split]["cost_per_correct"]
            if cost_per_correct > 1000:
                recommendations.append(f"High cost per correct ({cost_per_correct:.0f} tokens) on {split} - optimize token usage")
    
    return recommendations

def main():
    """Main analysis function"""
    print("🔍 Phase 3.4 Analysis: Override Pattern Study and Threshold Optimization")
    print("=" * 80)
    
    # Load all hybrid runs
    runs = load_hybrid_runs()
    print(f"📊 Found {len(runs)} hybrid mode runs for analysis")
    
    if not runs:
        print("❌ No hybrid runs found. Run some hybrid evaluations first.")
        return
    
    # Analyze each run
    all_metrics = []
    all_recommendations = []
    
    for run in runs:
        print(f"\n📁 Analyzing run: {run['run_name']}")
        print(f"   Mode: {run['mode']}")
        print(f"   Dev accuracy: {run.get('dev_accuracy', 'N/A')}")
        print(f"   Test accuracy: {run.get('test_accuracy', 'N/A')}")
        
        # Analyze override patterns
        patterns = analyze_override_patterns(run["run_dir"])
        
        # Calculate cost metrics
        metrics = calculate_cost_metrics(patterns, run)
        
        # Generate recommendations
        recommendations = generate_optimization_recommendations(patterns, metrics)
        
        # Store results
        all_metrics.append({
            "run": run["run_name"],
            "metrics": metrics
        })
        all_recommendations.extend(recommendations)
        
        # Print detailed analysis
        for split in ["dev", "test"]:
            if split in patterns:
                print(f"   {split.upper()} Split:")
                print(f"     Total examples: {patterns[split]['total']}")
                print(f"     Overrides: {len(patterns[split]['overrides'])}")
                print(f"     Fallbacks: {len(patterns[split]['fallbacks'])}")
                
                if split in metrics:
                    m = metrics[split]
                    print(f"     Override rate: {m['override_rate']:.1%}")
                    print(f"     Override success: {m['override_success_rate']:.1%}")
                    print(f"     Cost per correct: {m['cost_per_correct']:.0f} tokens")
    
    # Summary and recommendations
    print("\n" + "=" * 80)
    print("🎯 PHASE 3.4 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    
    if all_recommendations:
        for i, rec in enumerate(all_recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("✅ No immediate optimization recommendations - system performing well!")
    
    # Next steps
    print("\n🚀 NEXT STEPS FOR PHASE 3.4:")
    print("1. Implement confidence score logging in evaluator")
    print("2. Test different confidence thresholds (0.25, 0.30, 0.40)")
    print("3. Analyze confidence distribution patterns")
    print("4. Optimize scoring criteria based on empirical data")
    print("5. Implement conditional execution based on confidence levels")

if __name__ == "__main__":
    main()
