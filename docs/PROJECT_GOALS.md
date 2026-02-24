# Capstone Goals and Scope

## 1. Goal

Build a **lightweight, workload-aware Partitioning Advisor** that recommends strategy and configuration.

Experiment and data-collection flow: [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md).

---

## 2. Input (current and extensible)

- **Current**: Query type (aggregation / join / window), data size (e.g. 5mb, 50mb, 500mb, 5gb).
- **Extensible**: SQL/query patterns, filters, more workload features.

## 3. Output

- Recommended strategy: **Hive partition vs Spark repartition**.
- Configuration: e.g. **partition count** (4 / 16 / 32) when using repartition.
- Optional: explanation or confidence for a given objective (runtime / cpu / memory).

## 4. Value

Given a workload, **automatically suggest a better partitioning/repartition choice**, reducing manual tuning and trial-and-error.

---

## 5. Feedback (direction)

- **Direction endorsed**: “build a lightweight, workload-aware advisor”.
- **Further suggestion**: Train a **model** to help with recommendations (e.g. learn (data_size, query_type, …) → best strategy/config from historical data).

---

## 6. Mapping to current implementation

| Concept              | Current implementation                                                                 |
| -------------------- | -------------------------------------------------------------------------------------- |
| Input: data size     | `advisor.py --data-size 5mb\|50mb\|500mb\|5gb`                                         |
| Input: query type    | `--query-type aggregate\|join\|window`                                                 |
| Input: objective     | `--objective runtime\|cpu\|memory`                                                     |
| Output: strategy     | `recommend()` returns `hive` or `spark_repartition`                                     |
| Output: partition #  | `num_partitions`: 4 / 16 / 32 (spark_repartition only)                                 |
| Recommendation basis | Rule-based choice from `experiment_summary.csv` (e.g. best row by objective)           |

Possible extensions:

- Finer query features (e.g. number of join keys, filter selectivity).
- A **model** trained on historical data to predict strategy or partition count, combined with the current rules.
