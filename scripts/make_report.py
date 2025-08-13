import argparse, json, pathlib, pandas as pd
import matplotlib.pyplot as plt

def load_summaries(runs_dir: pathlib.Path):
    rows = []
    for run in runs_dir.iterdir():
        s = run / "summary.json"
        if s.exists():
            j = json.loads(s.read_text())
            j["run"] = run.name
            rows.append(j)
    return pd.DataFrame(rows)

def calculate_cost_metrics(df: pd.DataFrame, runs_dir: pathlib.Path):
    """Calculate tokens per correct and cost per 100 correct metrics by reading actual records"""
    # Extract mode from run name
    df['mode'] = df['run'].str.extract(r'_(\w+)$')
    
    # Calculate tokens per correct for each run by reading actual records
    for idx, row in df.iterrows():
        run_name = row['run']
        run_dir = runs_dir / run_name
        
        # Try to read dev records first, then test records
        records_path = None
        if (run_dir / "dev" / "records.jsonl").exists():
            records_path = run_dir / "dev" / "records.jsonl"
            accuracy = row.get('dev_accuracy', 0)
        elif (run_dir / "test" / "records.jsonl").exists():
            records_path = run_dir / "test" / "records.jsonl"
            accuracy = row.get('test_accuracy', 0)
        else:
            # Fallback to summary data
            accuracy = row.get('dev_accuracy', row.get('test_accuracy', 0))
            tokens = row.get('dev_avg_tokens_out', row.get('test_avg_tokens_out', 0))
            
            if accuracy > 0 and tokens and tokens > 0:
                df.loc[idx, 'tokens_per_correct'] = tokens / accuracy
                price_per_token = 0.002 / 1000
                df.loc[idx, 'cost_per_100_correct'] = (tokens / accuracy) * price_per_token * 100
            else:
                df.loc[idx, 'tokens_per_correct'] = float('inf')
                df.loc[idx, 'cost_per_100_correct'] = float('inf')
            continue
        
        if records_path and records_path.exists():
            # Read actual records to get true token counts
            total_tokens = 0
            correct_count = 0
            
            try:
                with open(records_path, 'r') as f:
                    for line in f:
                        record = json.loads(line.strip())
                        if record.get('correct', 0) == 1:
                            correct_count += 1
                        
                        # Extract total tokens based on strategy
                        usage = record.get('usage', {})
                        if isinstance(usage, dict):
                            if 'total_tokens_all_calls' in usage:
                                # Self-Refine or Distillation mode
                                total_tokens += usage.get('total_tokens_all_calls', 0)
                            else:
                                # Baseline/GEPA mode - single call
                                input_tokens = usage.get('input_tokens', 0)
                                output_tokens = usage.get('output_tokens', 0)
                                total_tokens += input_tokens + output_tokens
                        else:
                            # Fallback
                            total_tokens += usage if usage else 0
                
                # Calculate metrics
                if correct_count > 0 and total_tokens > 0:
                    df.loc[idx, 'tokens_per_correct'] = total_tokens / correct_count
                    price_per_token = 0.002 / 1000
                    df.loc[idx, 'cost_per_100_correct'] = (total_tokens / correct_count) * price_per_token * 100
                else:
                    df.loc[idx, 'tokens_per_correct'] = float('inf')
                    df.loc[idx, 'cost_per_100_correct'] = float('inf')
                    
            except Exception as e:
                print(f"Error processing {records_path}: {e}")
                df.loc[idx, 'tokens_per_correct'] = float('inf')
                df.loc[idx, 'cost_per_100_correct'] = float('inf')
    
    return df

def plot_pareto(runs_dir: pathlib.Path, out_path: pathlib.Path):
    # Find latest GEPA run; look for round1/variants.json
    gepa_runs = sorted([p for p in runs_dir.iterdir() if p.name.endswith("_gepa")], reverse=True)
    if not gepa_runs:
        return
    latest = gepa_runs[0]
    var_path = latest / "round1" / "variants.json"
    if not var_path.exists():
        return
    j = json.loads(var_path.read_text())
    df = pd.DataFrame(j["variants"])
    fig = plt.figure()
    plt.scatter(df["avg_tokens_out"], df["accuracy"])
    for _, r in df.iterrows():
        plt.text(r["avg_tokens_out"], r["accuracy"], r["name"])
    plt.xlabel("Avg output tokens (dev)")
    plt.ylabel("Accuracy (dev)")
    plt.title("Variant Pareto Scatter (GEPA round 1)")
    fig.savefig(out_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_dir", type=str, default="runs")
    ap.add_argument("--out", type=str, default="report/results.md")
    args = ap.parse_args()

    runs_dir = pathlib.Path(args.runs_dir)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    df = load_summaries(runs_dir)
    
    # Calculate cost metrics
    df = calculate_cost_metrics(df, runs_dir)
    
    # Save enhanced summary
    df.to_csv(out.parent / "summary.csv", index=False)

    plot_pareto(runs_dir, out.parent / "pareto.png")

    # Generate enhanced markdown report
    md = ["# Results",
          "",
          "## Summary with Cost Metrics",
          "",
          "| Run | Mode | Dev Accuracy | Test Accuracy | Avg Tokens | Tokens/Correct | Cost/100 Correct |",
          "|-----|------|--------------|---------------|------------|----------------|------------------|"]
    
    # Add rows for each run
    for _, row in df.iterrows():
        run_name = row['run']
        mode = row.get('mode', 'unknown')
        dev_acc = row.get('dev_accuracy', 'N/A')
        test_acc = row.get('test_accuracy', 'N/A')
        
        # Get tokens from dev or test
        avg_tokens = row.get('dev_avg_tokens_out', row.get('test_avg_tokens_out', 'N/A'))
        tokens_per_correct = row.get('tokens_per_correct', 'N/A')
        cost_per_100 = row.get('cost_per_100_correct', 'N/A')
        
        if isinstance(tokens_per_correct, float) and tokens_per_correct == float('inf'):
            tokens_per_correct = '∞'
        if isinstance(cost_per_100, float) and cost_per_100 == float('inf'):
            cost_per_100 = '∞'
        
        # Handle cost formatting safely
        if isinstance(cost_per_100, (int, float)) and cost_per_100 != float('inf'):
            cost_str = f"${cost_per_100:.4f}"
        else:
            cost_str = str(cost_per_100)
        
        md.append(f"| {run_name} | {mode} | {dev_acc} | {test_acc} | {avg_tokens} | {tokens_per_correct} | {cost_str} |")
    
    md.extend([
        "",
        "## Key Insights",
        "",
        "- **Tokens per Correct**: Lower is better - combines cost and accuracy",
        "- **Cost per 100 Correct**: Dollar cost for 100 correct answers",
        "- **Self-Refine vs GEPA**: Compare efficiency at similar accuracy levels",
        "",
        "## GEPA Variant Pareto",
        "",
        "See `pareto.png` for the scatter plot."
    ])
    out.write_text("\n".join(md))
    print("Wrote", out)

if __name__ == "__main__":
    main()
