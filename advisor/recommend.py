"""
Recommend partitioning strategy from experiment_summary.csv.
Usage: recommend(data_size, query_type, objective="runtime") -> (strategy, num_partitions, reason, row)
"""

import os
import csv
from typing import Optional, Tuple, Any


def _norm_size(s: str) -> str:
    return str(s).strip().lower() if s else ""


def _norm_qtype(s: str) -> str:
    return str(s).strip().lower() if s else ""


def _float_or_none(s: Any) -> Optional[float]:
    if s is None or (isinstance(s, str) and s.strip() == ""):
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def load_summary(csv_path: str) -> list:
    """Load experiment_summary.csv into list of dicts."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["data_size"] = _norm_size(r.get("data_size", ""))
            r["query_type"] = _norm_qtype(r.get("query_type", ""))
            r["strategy"] = (r.get("strategy") or "").strip().lower()
            raw_np = r.get("num_partitions")
            r["num_partitions"] = int(raw_np) if raw_np and str(raw_np).strip() else None
            r["runtime_seconds"] = _float_or_none(r.get("runtime_seconds"))
            r["max_cpu_pct"] = _float_or_none(r.get("max_cpu_pct"))
            r["max_memory_mib"] = _float_or_none(r.get("max_memory_mib"))
            rows.append(r)
    return rows


def recommend(
    data_size: str,
    query_type: str,
    objective: str = "runtime",
    summary_path: Optional[str] = None,
) -> Tuple[str, Optional[int], str, dict]:
    """
    Recommend best strategy for given data_size and query_type.

    Returns:
        (strategy, num_partitions, reason, row)
        - strategy: "hive" or "spark_repartition"
        - num_partitions: 4/16/32 for spark_repartition, None for hive
        - reason: short explanation
        - row: full summary row (for CLI display)

    Raises:
        FileNotFoundError: if summary CSV not found
        ValueError: if no matching experiments for (data_size, query_type)
    """
    if summary_path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        summary_path = os.path.join(base, "experiment_summary.csv")
    if not os.path.isfile(summary_path):
        raise FileNotFoundError(f"Summary not found: {summary_path}")

    data_size = _norm_size(data_size)
    query_type = _norm_qtype(query_type)
    objective = (objective or "runtime").strip().lower()

    rows = load_summary(summary_path)
    subset = [
        r
        for r in rows
        if r["data_size"] == data_size and r["query_type"] == query_type and r["runtime_seconds"] is not None
    ]
    if not subset:
        raise ValueError(
            f"No experiments for data_size={data_size!r} query_type={query_type!r}. "
            f"Valid: data_size in 5mb,50mb,500mb,5gb; query_type in aggregate,join,window"
        )

    if objective == "runtime":
        best = min(subset, key=lambda r: r["runtime_seconds"])
    elif objective == "cpu" or objective == "max_cpu":
        with_cpu = [r for r in subset if r["max_cpu_pct"] is not None]
        if with_cpu:
            best = min(with_cpu, key=lambda r: r["max_cpu_pct"])
        else:
            best = min(subset, key=lambda r: r["runtime_seconds"])
    elif objective == "memory" or objective == "max_memory":
        with_mem = [r for r in subset if r["max_memory_mib"] is not None]
        if with_mem:
            best = min(with_mem, key=lambda r: r["max_memory_mib"])
        else:
            best = min(subset, key=lambda r: r["runtime_seconds"])
    else:
        best = min(subset, key=lambda r: r["runtime_seconds"])

    strategy = best["strategy"]
    num_partitions = best["num_partitions"]
    rt = best["runtime_seconds"]
    if strategy == "hive":
        reason = f"Lowest runtime ({rt:.1f}s) for {data_size} {query_type} in experiments: use Hive partitioned table."
    else:
        reason = f"Lowest runtime ({rt:.1f}s) for {data_size} {query_type} in experiments: use Spark repartition({num_partitions})."
    return strategy, num_partitions, reason, best
