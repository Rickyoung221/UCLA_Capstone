# Partitioning Advisor Design

This document describes the **Workload-Aware Partitioning Advisor**: inputs/outputs, rule logic, data dependency, and evaluation, for reproduction and reporting.

---

## 1. Goal and scope

- **Goal**: Given workload (data size + query type), recommend a partitioning strategy and configuration to reduce manual tuning.
- **Scope**: Lightweight, **rule/lookup-based** advisor (V1) over the experiment summary table; not a general SQL optimizer; only for “Hive partition vs Spark repartition + partition count”.
- **Patterns**: See [ADVISOR_PATTERNS.md](ADVISOR_PATTERNS.md) for scale/query-type/partition-count patterns.

---

## 2. Input and output

### 2.1 Input

| Parameter      | Meaning        | Values                              |
| -------------- | -------------- | ----------------------------------- |
| `data_size`    | Data scale     | 5mb / 50mb / 500mb / 5gb            |
| `query_type`   | Query type     | aggregate / join / window           |
| `objective` (optional) | Optimize for | runtime (default) / cpu / memory     |

### 2.2 Output

| Output          | Meaning                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| `strategy`      | Recommended strategy: `hive` or `spark_repartition`                      |
| `num_partitions`| 4 / 16 / 32 when strategy is spark_repartition; None for Hive           |
| `reason`        | Short explanation (e.g. “Lowest runtime for 50mb join: use Spark repartition(4).”) |
| `row`           | Full summary row (runtime_seconds, max_cpu_pct, max_memory_mib, etc.) for CLI details |

---

## 3. Rule logic (V1 lookup)

- **Data**: Read `advisor/experiment_summary.csv` (produced by `advisor/scripts/build_summary.py` from `*_results.csv` and `*_stats/*.csv` under `stats_collection_tools/`).
- **Filter**: For given `(data_size, query_type)`, keep only rows for that combination with non-empty `runtime_seconds`.
- **Choose best**: By `objective`:
  - **runtime**: Row with minimum `runtime_seconds`.
  - **cpu**: Row with minimum `max_cpu_pct` if present; else fall back to minimum runtime.
  - **memory**: Row with minimum `max_memory_mib` if present; else fall back to minimum runtime.
- **Return**: That row’s `strategy`, `num_partitions`, and a generated `reason` and full `row`.

Raises `ValueError` if no matching row exists (e.g. data_size/query_type not in the experiment set).

---

## 4. Data and table structure

### 4.1 Summary table path

- Default: `advisor/experiment_summary.csv`.
- CLI and `recommend()` accept a custom path via `--summary` / `summary_path`.

### 4.2 experiment_summary.csv schema

| Column           | Meaning                                          |
| ---------------- | ------------------------------------------------ |
| data_size        | 5mb / 50mb / 500mb / 5gb                         |
| query_type       | aggregate / join / window                        |
| strategy         | hive / spark_repartition                         |
| num_partitions   | 4 / 16 / 32 (spark_repartition only); empty for Hive |
| runtime_seconds  | Minimum runtime (seconds) for this combination   |
| max_cpu_pct      | Max CPU usage (%), optional                      |
| max_memory_mib   | Max memory (MiB), optional                       |

Data source and reproduction: [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md).

---

## 5. Evaluation method and results

### 5.1 Method

- For each `(data_size, query_type)` in the summary, call `recommend(..., objective="runtime")` and compare to the true best row for that combination (by runtime). If the recommended strategy and partition count match the true best, count as agreement.
- **Script**: `advisor/scripts/evaluate_advisor.py`.
- **Run** (from project root): `python3 advisor/scripts/evaluate_advisor.py`

### 5.2 Results (objective=runtime)

With the current `advisor/experiment_summary.csv`, the script produces:

| data_size | query_type | Advisor recommendation      | True best                   | Match |
| --------- | ---------- | --------------------------- | --------------------------- | ----- |
| 500mb     | aggregate  | spark_repartition n=4       | spark_repartition n=4       | Yes   |
| 500mb     | join       | spark_repartition n=16      | spark_repartition n=16      | Yes   |
| 500mb     | window     | hive                        | hive                        | Yes   |
| 50mb      | aggregate  | spark_repartition n=4       | spark_repartition n=4       | Yes   |
| 50mb      | join       | spark_repartition n=4       | spark_repartition n=4       | Yes   |
| 50mb      | window     | spark_repartition n=16      | spark_repartition n=16      | Yes   |
| 5gb       | aggregate  | hive                        | hive                        | Yes   |
| 5gb       | join       | hive                        | hive                        | Yes   |
| 5gb       | window     | hive                        | hive                        | Yes   |
| 5mb       | aggregate  | spark_repartition n=32      | spark_repartition n=32      | Yes   |
| 5mb       | join       | spark_repartition n=4       | spark_repartition n=4       | Yes   |
| 5mb       | window     | spark_repartition n=4       | spark_repartition n=4       | Yes   |

**Agreement rate: 12/12 = 100.0%**

(On the current experiment set, the Advisor’s recommendation matches the runtime-optimal configuration in the summary; suitable for use in reports.)

---

## 6. Limitations and future work

- **Limitations**: Single cluster; three query types (aggregate/join/window); fixed schema; recommendations depend entirely on the existing summary table; no SQL parsing or live cluster state.
- **Future work**: (1) Train a simple model from experiment_summary (e.g. decision tree / random forest) as V2 and compare to the rule-based advisor; (2) add more configuration dimensions (e.g. spark.sql.shuffle.partitions, more repartition counts); (3) skew-aware tuning or more query types and data scales.
