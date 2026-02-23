#!/usr/bin/env python3
"""
CLI for Partitioning Advisor: recommend strategy from data_size and query_type.

Usage (from project root):
  python3 advisor/advisor.py --data-size 50mb --query-type join
  python3 advisor/advisor.py --data-size 5mb --query-type window --objective runtime
"""

import argparse
import os
import sys


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    default_summary = os.path.join(base, "experiment_summary.csv")

    parser = argparse.ArgumentParser(
        description="Partitioning Advisor: recommend Hive vs Spark repartition by data size and query type."
    )
    parser.add_argument("--data-size", "-s", required=True, help="Data size: 5mb, 50mb, 500mb, 5gb")
    parser.add_argument("--query-type", "-q", required=True, choices=["aggregate", "join", "window"], help="Query type")
    parser.add_argument(
        "--objective", "-o",
        default="runtime",
        choices=["runtime", "cpu", "memory"],
        help="Optimize for: runtime (default), cpu, or memory",
    )
    parser.add_argument("--summary", default=default_summary, help=f"Path to experiment_summary.csv (default: {default_summary})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print full row (runtime, max_cpu, max_memory)")
    args = parser.parse_args()

    try:
        from recommend import recommend
    except ImportError:
        # when run as script, advisor/ is cwd or in path
        sys.path.insert(0, base)
        from recommend import recommend

    try:
        strategy, num_partitions, reason, row = recommend(
            args.data_size,
            args.query_type,
            objective=args.objective,
            summary_path=args.summary,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Run from project root: python3 advisor/scripts/build_summary.py", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print("Recommendation:")
    print(f"  strategy:        {strategy}")
    print(f"  num_partitions:  {num_partitions if num_partitions is not None else '(N/A for Hive)'}")
    print(f"  reason:         {reason}")
    if args.verbose:
        print("  details:         runtime_seconds={}, max_cpu_pct={}, max_memory_mib={}".format(
            row.get("runtime_seconds"),
            row.get("max_cpu_pct"),
            row.get("max_memory_mib"),
        ))


if __name__ == "__main__":
    main()
