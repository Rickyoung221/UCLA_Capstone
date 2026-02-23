#!/usr/bin/env python3
"""
根据 experiment_summary.csv 画 runtime 对比图，用于报告/论文。

依赖：matplotlib（pip install matplotlib）
从项目根目录运行：
  python3 advisor/scripts/plot_runtime.py
  python3 advisor/scripts/plot_runtime.py -o report_figure.png
"""

import os
import sys
import csv
import argparse

# 保证能定位到 advisor 目录
_script_dir = os.path.dirname(os.path.abspath(__file__))
_advisor_dir = os.path.dirname(_script_dir)


def load_summary(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rt = r.get("runtime_seconds")
            if rt is None or (isinstance(rt, str) and rt.strip() == ""):
                continue
            try:
                r["runtime_seconds"] = float(rt)
            except (TypeError, ValueError):
                continue
            r["data_size"] = (r.get("data_size") or "").strip().lower()
            r["query_type"] = (r.get("query_type") or "").strip().lower()
            r["strategy"] = (r.get("strategy") or "").strip().lower()
            np_val = r.get("num_partitions")
            r["num_partitions"] = int(np_val) if np_val and str(np_val).strip() else None
            rows.append(r)
    return rows


def strategy_label(r):
    if r["strategy"] == "hive":
        return "Hive"
    n = r.get("num_partitions")
    return f"Spark-{n}" if n is not None else "Spark"


def main():
    parser = argparse.ArgumentParser(description="Plot runtime comparison from experiment_summary.csv")
    default_csv = os.path.join(_advisor_dir, "experiment_summary.csv")
    parser.add_argument("--summary", "-s", default=default_csv, help="Path to experiment_summary.csv")
    parser.add_argument("--output", "-o", default=None, help="Output path (default: advisor/scripts/runtime_comparison.png)")
    parser.add_argument("--dpi", type=int, default=150, help="Figure DPI for saved image")
    args = parser.parse_args()

    if not os.path.isfile(args.summary):
        print(f"Error: not found {args.summary}", file=sys.stderr)
        sys.exit(1)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError as e:
        print("Error: matplotlib required. Run: pip install matplotlib", file=sys.stderr)
        print(f"  ({e})", file=sys.stderr)
        sys.exit(1)

    rows = load_summary(args.summary)
    if not rows:
        print("No rows with runtime in summary.", file=sys.stderr)
        sys.exit(1)

    # 按 query_type 分三组，x = data_size（从数据中取，顺序：5mb, 50mb, 500mb, 5gb）
    size_order = ["5mb", "50mb", "500mb", "5gb"]
    all_sizes = set(r["data_size"] for r in rows)
    sizes = [s for s in size_order if s in all_sizes] or sorted(all_sizes)
    qtypes = ["aggregate", "join", "window"]
    strategies = ["Hive", "Spark-4", "Spark-16", "Spark-32"]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.suptitle("Runtime by strategy (Hive vs Spark repartition)", fontsize=12)

    for qi, qtype in enumerate(qtypes):
        ax = axes[qi]
        ax.set_title(qtype.capitalize())
        ax.set_ylabel("Runtime (s)")
        ax.set_xlabel("Data size")

        x = list(range(len(sizes)))
        width = 0.2
        offsets = [-1.5, -0.5, 0.5, 1.5]
        for si, strat in enumerate(strategies):
            vals = []
            for data_size in sizes:
                val = None
                for r in rows:
                    if r["data_size"] != data_size or r["query_type"] != qtype:
                        continue
                    if strat == "Hive" and r["strategy"] == "hive":
                        val = r["runtime_seconds"]
                        break
                    if strat.startswith("Spark-"):
                        n = int(strat.split("-")[1])
                        if r["strategy"] == "spark_repartition" and r.get("num_partitions") == n:
                            val = r["runtime_seconds"]
                            break
                vals.append(val if val is not None else 0)
            pos = [xi + offsets[si] * width for xi in x]
            bars = ax.bar(pos, vals, width=width, label=strat)
            for b in bars:
                if b.get_height() == 0:
                    b.set_visible(False)

        ax.set_xticks(x)
        ax.set_xticklabels(sizes)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out = args.output or os.path.join(_script_dir, "runtime_comparison.png")
    plt.savefig(out, dpi=args.dpi, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
