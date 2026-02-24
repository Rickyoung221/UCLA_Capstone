# Experiment Design (Data Source for experiment_summary.csv)

This document describes the **data source**, **metric definitions**, and **reproduction steps** for `experiment_summary.csv`, for use by the Advisor and reports.

---

## 1. Summary Table Schema

| Column            | Meaning                                                                        |
| ----------------- | ------------------------------------------------------------------------------ |
| `data_size`       | Data scale: 5mb / 50mb / 500mb / 5gb                                           |
| `query_type`      | Query type: aggregate / join / window                                          |
| `strategy`        | Partitioning strategy: hive (native Hive) or spark_repartition (explicit)      |
| `num_partitions`  | Only when strategy=spark_repartition: 4 / 16 / 32; empty for Hive              |
| `runtime_seconds` | **Minimum** runtime (seconds) over runs for this combination                   |
| `max_cpu_pct`     | Max container CPU usage (%) during the task, from \*_stats samples             |
| `max_memory_mib`  | Max container memory (MiB) during the task, from \*_stats samples              |

---

## 2. Data Sources

### 2.1 Runtime (runtime_seconds)

- **Source**: `5mb_results.csv`, `50mb_results.csv`, `500mb_results.csv`, `5gb_results.csv` under `stats_collection_tools/`.
- **Raw columns**: Each row has `name` (e.g. `Test50MB_Join_16`) and `runtime_seconds`.
- **Parsing**:
  - `Test{size}MB_{Aggregate|Join|Window}` → data_size={size}mb, query_type=aggregate|join|window, strategy=hive, num_partitions=empty.
  - `Test{size}MB_{Aggregate|Join|Window}_{N}` → same, but strategy=spark_repartition, num_partitions=N (4/16/32).
- **Aggregation**: For each (data_size, query_type, strategy, num_partitions), take the **minimum** runtime_seconds as the best runtime.

### 2.2 Resource usage (max_cpu_pct, max_memory_mib)

- **Source**: CSV files under `stats_collection_tools/{5mb,50mb,500mb}_stats/` and `2gb_stats/` (5gb stats use filenames `5gb-*.csv`).
- **Naming**:
  - `{size}-hive-task-{1|2|3}.csv` → data_size={size}, query_type=aggregate|join|window (1→aggregate, 2→join, 3→window), strategy=hive.
  - `{size}-no-hive-task-{1|2|3}-{N}.csv` → same, strategy=spark_repartition, num_partitions=N.
- **Metrics**: For each CSV, exclude rows with Container=ALL; take max CPUPerc and max MemUsage (converted to MiB) over time. If no stats file exists for a combination, max_cpu_pct / max_memory_mib are empty.

---

## 3. Experiment Combinations and Reproduction

- **Data scales**: 5mb, 50mb, 500mb (and 5gb; see note below), corresponding to partitioned table/CSV size on HDFS.
- **Query types**:
  - **aggregate**: GROUP BY aggregation (see `sql/aggregate.sql` / hive-task1 / no-hive-task1).
  - **join**: Multi-column equality + range JOIN (see `sql/join.sql` / hive-task2 / no-hive-task2).
  - **window**: Window functions ROW_NUMBER / SUM OVER (see `sql/window.sql` / hive-task3 / no-hive-task3).
- **Strategies**:
  - **hive**: Hive partitioned table; Spark reads from Hive and runs the SQL.
  - **spark_repartition**: Read CSV from HDFS, `df.repartition(N)`, create temp view, run same SQL; N=4/16/32.

To reproduce: run tasks in the Docker cluster via `hive-file-gen.py` / `no-hive-file-gen.py`, collect application names and runtimes from YARN/Spark History, collect container CPU/memory (e.g. `docker stats` or existing scripts) for the corresponding time windows, produce new \_results.csv and \_stats/\*.csv, then run the summary script to update experiment_summary.csv.

---

## 4. Generating / Updating experiment_summary.csv

From the project root:

```bash
python3 advisor/scripts/build_summary.py
```

Output is written to `advisor/experiment_summary.csv` by default. Optional arguments:

- `--project-root <path>`: Project root (default: two levels up from the script).
- `-o <path>`: Output CSV path.

The script uses only the Python 3 standard library (no pandas).

**5gb note**: The runtime in `5gb_results.csv` is currently a placeholder from existing 2GB-scale experiments so that 5gb appears in the summary; 5gb CPU/memory come from existing `5gb-*.csv` under `2gb_stats/`. If you run real 5GB experiments and have YARN/History data, replace `5gb_results.csv` and run `build_summary.py` again.
