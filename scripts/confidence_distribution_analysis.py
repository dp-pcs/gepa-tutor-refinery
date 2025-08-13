#!/usr/bin/env python3
"""
Phase 3.4: Confidence Distribution Analysis
Analyze confidence scores for successful vs. failed runs to identify patterns
"""

import json
import pathlib
from collections import defaultdict
import statistics

def analyze_confidence_distributions(runs_dir="runs"):
    """Analyze confidence distributions for successful vs. failed runs"""
    runs_path = pathlib.Path(runs_dir)
    
    # Collect confidence data from all hybrid runs
    confidence_data = {
        "successful_overrides": [],
        "failed_overrides": [],
        "fallbacks": [],
        "runs_analysis": []
    }
    
    for run_dir in runs_path.iterdir():
        if not run_dir.is_dir() or "hybrid" not in run_dir.name:
            continue
            
        print(f"📁 Analyzing confidence distributions in: {run_dir.name}")
        
        run_data = {
            "run_name": run_dir.name,
            "successful_overrides": [],
            "failed_overrides": [],
            "fallbacks": [],
            "total_examples": 0
        }
        
        # Analyze dev and test splits
        for split in ["dev", "test"]:
            records_file = run_dir / split / "records.jsonl"
            if not records_file.exists():
                continue
                
            with open(records_file) as f:
                for line in f:
                    record = json.loads(line)
                    run_data["total_examples"] += 1
                    
                    usage = record.get("usage", {})
                    confidence = usage.get("gepa_confidence")
                    
                    if confidence is None:
                        # This is a fallback (no GEPA confidence available)
                        confidence_data["fallbacks"].append({
                            "run": run_dir.name,
                            "split": split,
                            "id": record["id"],
                            "correct": record["correct"]
                        })
                        run_data["fallbacks"].append({
                            "confidence": None,
                            "correct": record["correct"]
                        })
                        continue
                    
                    # Check if this was an override
                    sr_output = usage.get("sr_output", "")
                    gepa_output = usage.get("gepa_output", "")
                    
                    if sr_output and gepa_output:
                        # Extract answers to determine if override occurred
                        sr_answer = extract_answer(sr_output)
                        gepa_answer = extract_answer(gepa_output)
                        
                        # Debug: Print what we're finding
                        if record["id"] in ["truthfulqa:288", "truthfulqa:215", "truthfulqa:689", "truthfulqa:406"]:
                            print(f"DEBUG {record['id']}: SR='{sr_answer}' vs GEPA='{gepa_answer}', confidence={confidence}")
                        
                        # Check if GEPA actually changed the answer
                        if sr_answer != gepa_answer and gepa_answer:
                            # This was an override attempt
                            if record["correct"]:
                                # Successful override
                                confidence_data["successful_overrides"].append({
                                    "run": run_dir.name,
                                    "split": split,
                                    "id": record["id"],
                                    "confidence": confidence,
                                    "correct": record["correct"]
                                })
                                run_data["successful_overrides"].append({
                                    "confidence": confidence,
                                    "correct": record["correct"]
                                })
                            else:
                                # Failed override
                                confidence_data["failed_overrides"].append({
                                    "run": run_dir.name,
                                    "split": split,
                                    "id": record["id"],
                                    "confidence": confidence,
                                    "correct": record["correct"]
                                })
                                run_data["failed_overrides"].append({
                                    "confidence": confidence,
                                    "correct": record["correct"]
                                })
                        else:
                            # No override - fallback to SR
                            confidence_data["fallbacks"].append({
                                "run": run_dir.name,
                                "split": split,
                                "id": record["id"],
                                "confidence": confidence,
                                "correct": record["correct"]
                            })
                            run_data["fallbacks"].append({
                                "confidence": confidence,
                                "correct": record["correct"]
                            })
        
        confidence_data["runs_analysis"].append(run_data)
    
    return confidence_data

def extract_answer(text):
    """Extract answer letter from text"""
    import re
    match = re.search(r'Answer:\s*([A-Z])', text)
    return match.group(1) if match else None

def analyze_threshold_performance(confidence_data):
    """Analyze performance at different confidence thresholds"""
    thresholds = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    
    threshold_analysis = {}
    
    for threshold in thresholds:
        # Count overrides that would be accepted at this threshold
        accepted_overrides = [o for o in confidence_data["successful_overrides"] + confidence_data["failed_overrides"] 
                            if o["confidence"] >= threshold]
        
        if not accepted_overrides:
            continue
            
        successful = [o for o in accepted_overrides if o["correct"]]
        failed = [o for o in accepted_overrides if not o["correct"]]
        
        total = len(accepted_overrides)
        success_rate = len(successful) / total if total > 0 else 0
        
        threshold_analysis[threshold] = {
            "total_overrides": total,
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": success_rate,
            "confidence_range": {
                "min": min(o["confidence"] for o in accepted_overrides),
                "max": max(o["confidence"] for o in accepted_overrides),
                "avg": statistics.mean(o["confidence"] for o in accepted_overrides)
            }
        }
    
    return threshold_analysis

def print_confidence_analysis(confidence_data, threshold_analysis):
    """Print comprehensive confidence analysis"""
    print("🔍 PHASE 3.4: CONFIDENCE DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Overall statistics
    print(f"📊 OVERALL STATISTICS")
    print(f"   Total successful overrides: {len(confidence_data['successful_overrides'])}")
    print(f"   Total failed overrides: {len(confidence_data['failed_overrides'])}")
    print(f"   Total fallbacks: {len(confidence_data['fallbacks'])}")
    
    if confidence_data["successful_overrides"]:
        successful_confidences = [o["confidence"] for o in confidence_data["successful_overrides"]]
        print(f"   Successful override confidence range: {min(successful_confidences):.2f} - {max(successful_confidences):.2f}")
        print(f"   Successful override confidence avg: {statistics.mean(successful_confidences):.2f}")
    
    if confidence_data["failed_overrides"]:
        failed_confidences = [o["confidence"] for o in confidence_data["failed_overrides"]]
        print(f"   Failed override confidence range: {min(failed_confidences):.2f} - {max(failed_confidences):.2f}")
        print(f"   Failed override confidence avg: {statistics.mean(failed_confidences):.2f}")
    
    print()
    
    # Threshold performance analysis
    print(f"🎯 THRESHOLD PERFORMANCE ANALYSIS")
    print(f"   Threshold | Total | Success | Failed | Success Rate | Conf Range")
    print(f"   ---------|-------|---------|--------|--------------|------------")
    
    for threshold in sorted(threshold_analysis.keys()):
        data = threshold_analysis[threshold]
        conf_range = f"{data['confidence_range']['min']:.1f}-{data['confidence_range']['max']:.1f}"
        print(f"   {threshold:>8.2f} | {data['total_overrides']:>5} | {data['successful']:>7} | {data['failed']:>6} | {data['success_rate']:>11.1%} | {conf_range}")
    
    print()
    
    # Run-by-run analysis
    print(f"📁 RUN-BY-RUN ANALYSIS")
    for run_data in confidence_data["runs_analysis"]:
        print(f"   {run_data['run_name']}:")
        print(f"     Total examples: {run_data['total_examples']}")
        print(f"     Successful overrides: {len(run_data['successful_overrides'])}")
        print(f"     Failed overrides: {len(run_data['failed_overrides'])}")
        print(f"     Fallbacks: {len(run_data['fallbacks'])}")
        
        if run_data['successful_overrides']:
            confidences = [o["confidence"] for o in run_data['successful_overrides']]
            print(f"     Successful confidence range: {min(confidences):.2f} - {max(confidences):.2f}")
        
        if run_data['failed_overrides']:
            confidences = [o["confidence"] for o in run_data['failed_overrides']]
            print(f"     Failed confidence range: {min(confidences):.2f} - {max(confidences):.2f}")
        
        print()

def main():
    """Main analysis function"""
    print("🔍 Phase 3.4: Confidence Distribution Analysis")
    print("=" * 80)
    
    # Analyze confidence distributions
    confidence_data = analyze_confidence_distributions()
    
    # Analyze threshold performance
    threshold_analysis = analyze_threshold_performance(confidence_data)
    
    # Print comprehensive analysis
    print_confidence_analysis(confidence_data, threshold_analysis)
    
    # Recommendations
    print("🎯 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    
    if threshold_analysis:
        # Find optimal threshold
        best_threshold = max(threshold_analysis.keys(), 
                           key=lambda t: threshold_analysis[t]["success_rate"])
        best_success_rate = threshold_analysis[best_threshold]["success_rate"]
        
        print(f"1. OPTIMAL THRESHOLD: {best_threshold:.2f} (Success rate: {best_success_rate:.1%})")
        
        # Compare with current threshold
        current_threshold = 0.50
        if current_threshold in threshold_analysis:
            current_success_rate = threshold_analysis[current_threshold]["success_rate"]
            if best_threshold != current_threshold:
                improvement = best_success_rate - current_success_rate
                print(f"   Current threshold ({current_threshold:.2f}): {current_success_rate:.1%}")
                print(f"   Optimal threshold ({best_threshold:.2f}): {best_success_rate:.1%}")
                print(f"   Potential improvement: {improvement:+.1%}")
        
        print()
        print("2. CONFIDENCE FACTOR ANALYSIS:")
        
        # Analyze what makes successful overrides different
        if confidence_data["successful_overrides"] and confidence_data["failed_overrides"]:
            successful_avg = statistics.mean(o["confidence"] for o in confidence_data["successful_overrides"])
            failed_avg = statistics.mean(o["confidence"] for o in confidence_data["failed_overrides"])
            
            print(f"   Successful overrides avg confidence: {successful_avg:.2f}")
            print(f"   Failed overrides avg confidence: {failed_avg:.2f}")
            print(f"   Confidence gap: {successful_avg - failed_avg:.2f}")
            
            if successful_avg - failed_avg > 0.1:
                print("   ✅ Clear confidence separation - threshold optimization should work well")
            else:
                print("   ⚠️ Small confidence gap - may need scoring criteria refinement")
    
    print()
    print("3. NEXT STEPS:")
    print("   - Test optimal threshold on new runs")
    print("   - Refine confidence scoring if gap is small")
    print("   - Implement dataset-specific thresholds if needed")

if __name__ == "__main__":
    main()
