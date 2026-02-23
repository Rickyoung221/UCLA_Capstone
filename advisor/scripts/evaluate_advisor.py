#!/usr/bin/env python3
"""
Week 3 评估：对比 Advisor 推荐 vs 汇总表中 runtime 真实最优，输出一致率与表格。

从项目根目录运行：
  python3 advisor/scripts/evaluate_advisor.py
  python3 advisor/scripts/evaluate_advisor.py --summary advisor/experiment_summary.csv
"""

import os
import sys
import csv
import argparse

# 保证能 import recommend（从项目根或 advisor/ 运行）
_script_dir = os.path.dirname(os.path.abspath(__file__))
_advisor_dir = os.path.dirname(_script_dir)
if _advisor_dir not in sys.path:
    sys.path.insert(0, _advisor_dir)

from recommend import recommend, load_summary


def get_true_best_per_group(summary_path: str):
    """对每个 (data_size, query_type)，找到 runtime 最小的那一行。返回 dict: (data_size, query_type) -> row."""
    rows = load_summary(summary_path)
    best = {}
    for r in rows:
        rt = r.get("runtime_seconds")
        if rt is None:
            continue
        key = (r["data_size"], r["query_type"])
        if key not in best or rt < best[key]["runtime_seconds"]:
            best[key] = r
    return best


def strategy_key(row) -> tuple:
    """(strategy, num_partitions) 用于比较是否一致。"""
    s = (row.get("strategy") or "").strip().lower()
    np = row.get("num_partitions")
    if s == "hive":
        return ("hive", None)
    return ("spark_repartition", int(np) if np is not None else None)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Advisor: recommendation vs true best (runtime).")
    default_summary = os.path.join(_advisor_dir, "experiment_summary.csv")
    parser.add_argument("--summary", "-s", default=default_summary, help="Path to experiment_summary.csv")
    parser.add_argument("--objective", "-o", default="runtime", choices=["runtime", "cpu", "memory"])
    args = parser.parse_args()

    if not os.path.isfile(args.summary):
        print(f"Error: summary not found: {args.summary}", file=sys.stderr)
        sys.exit(1)

    true_best = get_true_best_per_group(args.summary)
    if not true_best:
        print("No rows with runtime in summary.", file=sys.stderr)
        sys.exit(1)

    results = []
    for (data_size, query_type), best_row in sorted(true_best.items()):
        try:
            strategy, num_partitions, reason, _ = recommend(
                data_size, query_type, objective=args.objective, summary_path=args.summary
            )
        except Exception as e:
            results.append((data_size, query_type, None, None, best_row, False, str(e)))
            continue
        rec_key = (strategy, num_partitions)
        best_key = strategy_key(best_row)
        match = rec_key == best_key
        results.append((data_size, query_type, strategy, num_partitions, best_row, match, None))

    # 输出表格
    print("Advisor 推荐 vs 真实最优 (objective={})".format(args.objective))
    print("-" * 80)
    print(f"{'data_size':<10} {'query_type':<12} {'Advisor 推荐':<28} {'真实最优':<28} {'一致'}")
    print("-" * 80)
    for data_size, query_type, rec_s, rec_np, best_row, match, err in results:
        if err:
            print(f"{data_size:<10} {query_type:<12} {'(error)':<28} {strategy_key(best_row)!s:<28} -")
            continue
        rec_str = rec_s + (f" n={rec_np}" if rec_np is not None else "")
        best_str = (best_row.get("strategy") or "") + (
            f" n={best_row.get('num_partitions')}" if best_row.get("num_partitions") is not None else ""
        )
        print(f"{data_size:<10} {query_type:<12} {rec_str:<28} {best_str:<28} {'是' if match else '否'}")
    print("-" * 80)

    matched = sum(1 for r in results if r[5] is True)
    total = len(results)
    rate = (matched / total * 100) if total else 0
    print(f"一致率: {matched}/{total} = {rate:.1f}%")
    print()
    print("（上表可直接用于报告/论文的评估部分。）")


if __name__ == "__main__":
    main()
