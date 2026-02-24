#!/usr/bin/env python3
"""
Build unified experiment summary from:
  - *_results.csv (runtime_seconds; name parsed for data_size, query_type, strategy, num_partitions)
  - *_stats/*.csv (max CPU, max memory per task)

Output: experiment_summary.csv with columns:
  data_size, query_type, strategy, num_partitions, runtime_seconds, max_cpu_pct, max_memory_mib

Run from project root: python3 advisor/scripts/build_summary.py
Uses only stdlib (no pandas required).
"""

import os
import re
import glob
import argparse
import csv
from collections import defaultdict


# Name pattern: Test5MB_Aggregate, Test50MB_Join_16, Test500MB_ExternalJoin_16
NAME_PATTERN = re.compile(r"^Test(\d+)(MB|GB)_(Aggregate|Join|Window|ExternalJoin)(?:_(\d+))?$", re.IGNORECASE)

# Stats filename pattern (basename without .csv): 5mb-hive-task-1, 50mb-no-hive-task-2-16, 5gb-hive-task-1
STATS_FILE_PATTERN = re.compile(r"^(\d+(?:mb|gb))-hive-task-([123])$", re.IGNORECASE)
STATS_FILE_PATTERN_NO_HIVE = re.compile(r"^(\d+(?:mb|gb))-no-hive-task-([123])-(\d+)$", re.IGNORECASE)

QUERY_MAP = {"1": "aggregate", "2": "join", "3": "window"}


def parse_memory(mem_str):
    if not mem_str or not str(mem_str).strip():
        return 0.0
    s = str(mem_str).strip()
    if "GiB" in s:
        return float(s.split("GiB")[0].strip()) * 1024
    if "MiB" in s:
        return float(s.split("MiB")[0].strip())
    return 0.0


def parse_result_name(name):
    """Parse name like Test5MB_Aggregate or Test50MB_Join_16 -> (data_size, query_type, strategy, num_partitions)."""
    m = NAME_PATTERN.match(name.strip())
    if not m:
        return None
    size_num, size_unit, qtype, num_part = m.group(1), m.group(2).lower(), m.group(3).lower(), m.group(4)
    if qtype == "externaljoin":
        qtype = "join"
    data_size = size_num + size_unit  # 5mb, 50mb, 500mb, 5gb
    if num_part is not None:
        return data_size, qtype, "spark_repartition", int(num_part)
    return data_size, qtype, "hive", None


def collect_runtime_rows(project_root):
    """Collect (data_size, query_type, strategy, num_partitions, runtime_seconds) from *_results.csv."""
    stats_dir = os.path.join(project_root, "stats_collection_tools")
    rows = []
    for f in ["5mb_results.csv", "50mb_results.csv", "500mb_results.csv", "5gb_results.csv"]:
        path = os.path.join(stats_dir, f)
        if not os.path.isfile(path):
            continue
        with open(path, newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for r in reader:
                name = r.get("name", "")
                parsed = parse_result_name(name)
                if parsed is None:
                    continue
                data_size, query_type, strategy, num_partitions = parsed
                try:
                    runtime = float(r.get("runtime_seconds", 0))
                except (TypeError, ValueError):
                    continue
                rows.append({
                    "data_size": data_size,
                    "query_type": query_type,
                    "strategy": strategy,
                    "num_partitions": num_partitions,
                    "runtime_seconds": runtime,
                })
    return rows


def aggregate_runtime_best(rows):
    """One row per (data_size, query_type, strategy, num_partitions) with minimum runtime."""
    best = {}
    for r in rows:
        key = (r["data_size"], r["query_type"], r["strategy"], r["num_partitions"])
        if key not in best or r["runtime_seconds"] < best[key]:
            best[key] = r["runtime_seconds"]
    return [
        {"data_size": k[0], "query_type": k[1], "strategy": k[2], "num_partitions": k[3], "runtime_seconds": v}
        for k, v in best.items()
    ]


def parse_stats_filename(basename):
    """From e.g. 50mb-hive-task-1 or 50mb-no-hive-task-2-16 -> (data_size, query_type, strategy, num_partitions)."""
    if not basename.lower().endswith(".csv"):
        return None
    name = basename[:-4]
    m = STATS_FILE_PATTERN.match(name)
    if m:
        data_size, task = m.group(1).lower(), m.group(2)
        return data_size, QUERY_MAP[task], "hive", None
    m = STATS_FILE_PATTERN_NO_HIVE.match(name)
    if m:
        data_size, task, num_part = m.group(1).lower(), m.group(2), m.group(3)
        return data_size, QUERY_MAP[task], "spark_repartition", int(num_part)
    return None


def collect_resource_from_stats(project_root):
    """Collect (data_size, query_type, strategy, num_partitions, max_cpu_pct, max_memory_mib) from *_stats/*.csv."""
    stats_base = os.path.join(project_root, "stats_collection_tools")
    pattern = os.path.join(stats_base, "*_stats", "*.csv")
    rows = []
    for path in glob.glob(pattern):
        if "fixed" in path or os.path.basename(path).startswith("fixed-"):
            continue
        basename = os.path.basename(path)
        parsed = parse_stats_filename(basename)
        if parsed is None:
            continue
        data_size, query_type, strategy, num_partitions = parsed
        try:
            max_cpu = 0.0
            max_mem = 0.0
            with open(path, newline="", encoding="utf-8") as fp:
                reader = csv.DictReader(fp)
                for r in reader:
                    if r.get("Container") == "ALL":
                        continue
                    cpustr = r.get("CPUPerc", "0").strip().rstrip("%") or "0"
                    try:
                        cpu = float(cpustr)
                    except ValueError:
                        cpu = 0.0
                    if cpu > max_cpu:
                        max_cpu = cpu
                    mem_str = r.get("MemUsage", "")
                    if "/" in mem_str:
                        mem_str = mem_str.split("/")[0].strip()
                    m = parse_memory(mem_str)
                    if m > max_mem:
                        max_mem = m
            rows.append({
                "data_size": data_size,
                "query_type": query_type,
                "strategy": strategy,
                "num_partitions": num_partitions,
                "max_cpu_pct": round(max_cpu, 2),
                "max_memory_mib": round(max_mem, 2),
            })
        except Exception as e:
            print(f"Skip {path}: {e}")
    return rows


def build_summary(project_root, output_path=None):
    if output_path is None:
        output_path = os.path.join(project_root, "advisor", "experiment_summary.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    runtime_rows = collect_runtime_rows(project_root)
    runtime_agg = aggregate_runtime_best(runtime_rows)
    resource_rows = collect_resource_from_stats(project_root)

    resource_by_key = {}
    for r in resource_rows:
        key = (r["data_size"], r["query_type"], r["strategy"], r["num_partitions"])
        resource_by_key[key] = r

    out_rows = []
    for r in runtime_agg:
        key = (r["data_size"], r["query_type"], r["strategy"], r["num_partitions"])
        res = resource_by_key.get(key, {})
        out_rows.append({
            "data_size": r["data_size"],
            "query_type": r["query_type"],
            "strategy": r["strategy"],
            "num_partitions": r["num_partitions"] if r["num_partitions"] is not None else "",
            "runtime_seconds": r["runtime_seconds"],
            "max_cpu_pct": res.get("max_cpu_pct", ""),
            "max_memory_mib": res.get("max_memory_mib", ""),
        })

    out_rows.sort(key=lambda x: (x["data_size"], x["query_type"], x["strategy"], x["num_partitions"] or 0))
    fieldnames = ["data_size", "query_type", "strategy", "num_partitions", "runtime_seconds", "max_cpu_pct", "max_memory_mib"]
    with open(output_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows to {output_path}")
    return output_path


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.dirname(os.path.dirname(script_dir))
    parser = argparse.ArgumentParser(description="Build experiment_summary.csv from results and stats.")
    parser.add_argument("--project-root", default=default_root, help="Project root")
    parser.add_argument("-o", "--output", default=None, help="Output CSV path (default: advisor/experiment_summary.csv)")
    args = parser.parse_args()
    build_summary(args.project_root, args.output)


if __name__ == "__main__":
    main()
