# Advisor 规律与推荐规则摘要

基于 `experiment_summary.csv` 与 CS 214 报告结论整理的规律，供 Advisor 说明与报告引用。

---

## 1. 按数据规模的规律

| 规模 | 建议倾向 | 说明 |
|------|----------|------|
| **5mb / 50mb** | 两者皆可，查表取最优 | Hive 与 Spark repartition 的 runtime 量级接近，实验中最优策略因 query 类型而异。 |
| **500mb** | 视 query 类型而定 | Aggregate 上 repartition(4) 可能优于 Hive；Join/Window 接近或 Hive 略稳。以汇总表最小 runtime 为准。 |
| **5gb（约 2GB）** | **优先 Hive** | 实验显示 Hive 约 8–12s，repartition 约 42–56s；Hive 约快 4–5 倍，I/O 与 shuffle 更少。 |

---

## 2. 按查询类型的规律

| 查询类型 | 规律 |
|----------|------|
| **Join** | 对策略最敏感；数据大时 Hive 优势明显（分区剪裁、join key 共位，减少 shuffle）。 |
| **Aggregate** | 中等规模下 repartition(4) 常有甜点；规模大时 Hive 更稳。 |
| **Window** | 与 Aggregate 类似；大数据量时 Hive 更省资源与时间。 |

---

## 3. 分区数（repartition 4/16/32）

- **4**：小到中规模下常为甜点，调度与 shuffle 开销小；500mb aggregate 上常优于 16/32。
- **16 / 32**：数据更大时与 4 接近或更慢；资源（CPU/内存）占用通常更高。
- **结论**：不盲目加大分区数；Advisor 按汇总表取该 (data_size, query_type) 下 runtime（或 cpu/memory）最优的配置。

---

## 4. Advisor 行为（V1 查表）

- 输入：`data_size`（5mb/50mb/500mb/5gb）、`query_type`（aggregate/join/window）、`objective`（runtime/cpu/memory）。
- 逻辑：在 `experiment_summary.csv` 中筛选该组合，按 `objective` 取最优一行（runtime 最小 / max_cpu 最小 / max_memory 最小）。
- 输出：推荐的 `strategy`（hive 或 spark_repartition）、`num_partitions`（若为 repartition）、`reason` 与对应行。

上述规律与实验数据一致；具体推荐以汇总表为准，本摘要用于解释「为什么这样推荐」。
