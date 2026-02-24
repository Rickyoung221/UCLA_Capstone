# Advisor Patterns and Recommendation Rules

Patterns derived from `experiment_summary.csv`, for Advisor explanation and report use.

---

## 1. By data scale

| Scale          | Tendency              | Notes                                                                 |
| -------------- | --------------------- | --------------------------------------------------------------------- |
| **5mb / 50mb** | Either; lookup best   | Hive and Spark repartition runtimes are similar; best varies by query. |
| **500mb**      | Depends on query type | repartition(4) often best for aggregate; join/window close or Hive better. Use min runtime in summary. |
| **5gb (~2GB)** | **Prefer Hive**       | Hive ~8–12s, repartition ~42–56s; Hive ~4–5× faster, less I/O and shuffle. |

---

## 2. By query type

| Query type  | Pattern                                                                 |
| ----------- | ----------------------------------------------------------------------- |
| **Join**    | Most sensitive to strategy; Hive wins at large scale (partition pruning, co-location, less shuffle). |
| **Aggregate** | repartition(4) often a sweet spot at medium scale; Hive more stable at large scale. |
| **Window**  | Similar to aggregate; Hive saves time and resources at large scale.     |

---

## 3. Partition count (repartition 4/16/32)

- **4**: Often the sweet spot at small–medium scale; lower scheduling and shuffle cost; often best for 500mb aggregate vs 16/32.
- **16 / 32**: At larger scale similar or slower than 4; usually higher CPU/memory use.
- **Conclusion**: Do not blindly increase partitions; the Advisor picks the (data_size, query_type) row with best runtime (or cpu/memory) in the summary.

---

## 4. Advisor behavior (V1 lookup)

- **Input**: `data_size` (5mb/50mb/500mb/5gb), `query_type` (aggregate/join/window), `objective` (runtime/cpu/memory).
- **Logic**: Filter the summary by that combination, choose the best row by `objective` (min runtime / min max_cpu / min max_memory).
- **Output**: Recommended `strategy` (hive or spark_repartition), `num_partitions` (if repartition), `reason`, and the corresponding row.

These patterns match the experiment data; the actual recommendation is always from the summary table; this document explains why a given recommendation is made.
