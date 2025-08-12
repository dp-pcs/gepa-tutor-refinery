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
    df.to_csv(out.parent / "summary.csv", index=False)

    plot_pareto(runs_dir, out.parent / "pareto.png")

    md = ["# Results",
          "",
          "## Summaries",
          "",
          f"See `summary.csv` for all runs.",
          "",
          "## GEPA Variant Pareto",
          "",
          "See `pareto.png` for the scatter plot."]
    out.write_text("\n".join(md))
    print("Wrote", out)

if __name__ == "__main__":
    main()
