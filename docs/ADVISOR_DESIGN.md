# Partitioning Advisor 设计说明

本文档说明 Capstone 延伸 **Workload-Aware Partitioning Advisor** 的输入/输出、规则逻辑、依赖数据与评估方式，供复现与报告使用。

---

## 1. 目标与定位

- **目标**：在给定 workload（数据规模 + 查询类型）下，自动推荐更合适的分区策略与配置，减少人工调参。
- **定位**：轻量级、基于实验汇总表的**规则/查表型**建议器（V1）；不做通用 SQL 优化器，只针对「Hive 分区 vs Spark repartition + partition 数」这一维度。
- **规律摘要**：规模/查询类型/分区数等规律见 [ADVISOR_PATTERNS.md](ADVISOR_PATTERNS.md)。

---

## 2. 输入与输出

### 2.1 输入

| 参数 | 含义 | 取值 |
|------|------|------|
| `data_size` | 数据规模 | 5mb / 50mb / 500mb |
| `query_type` | 查询类型 | aggregate / join / window |
| `objective`（可选） | 优化目标 | runtime（默认）/ cpu / memory |

### 2.2 输出

| 输出项 | 含义 |
|--------|------|
| `strategy` | 推荐策略：`hive` 或 `spark_repartition` |
| `num_partitions` | 仅当 strategy 为 spark_repartition 时有值：4 / 16 / 32；Hive 时为 None |
| `reason` | 简短理由（如 “Lowest runtime for 50mb join in experiments: use Spark repartition(4).”） |
| `row` | 汇总表中对应的完整一行（含 runtime_seconds、max_cpu_pct、max_memory_mib 等，供 CLI 详情展示） |

---

## 3. 规则逻辑（V1 查表）

- **数据来源**：读取 `advisor/experiment_summary.csv`（由 `advisor/scripts/build_summary.py` 从 `stats_collection_tools/` 下 `*_results.csv` 与 `*_stats/*.csv` 生成）。
- **筛选**：对给定 `(data_size, query_type)`，只保留该组合下、且 `runtime_seconds` 非空的记录。
- **选优**：按 `objective` 在筛选结果中取「最优」一行：
  - **runtime**：取 `runtime_seconds` 最小的行。
  - **cpu**：若有 `max_cpu_pct`，取 `max_cpu_pct` 最小的行；否则回退为 runtime 最小。
  - **memory**：若有 `max_memory_mib`，取 `max_memory_mib` 最小的行；否则回退为 runtime 最小。
- **返回**：该行的 `strategy`、`num_partitions`、以及根据该行生成的 `reason` 与完整 `row`。

未找到任何匹配记录时抛出 `ValueError`（例如 data_size/query_type 不在实验范围内）。

---

## 4. 依赖数据与表结构

### 4.1 汇总表路径

- 默认：`advisor/experiment_summary.csv`。
- CLI 与 `recommend()` 均支持通过参数指定其他路径（如 `--summary` / `summary_path`）。

### 4.2 experiment_summary.csv Schema

| 列名 | 含义 |
|------|------|
| data_size | 5mb / 50mb / 500mb |
| query_type | aggregate / join / window |
| strategy | hive / spark_repartition |
| num_partitions | 4 / 16 / 32（仅 spark_repartition）；Hive 为空 |
| runtime_seconds | 该组合下的最小运行时间（秒） |
| max_cpu_pct | 最大 CPU 使用率（%），可选 |
| max_memory_mib | 最大内存（MiB），可选 |

数据来源与复现方法见 [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md)。

---

## 5. 评估方式与结果

### 5.1 评估方式

- **方式**：在汇总表上，对每个出现的 `(data_size, query_type)` 调用 `recommend(..., objective="runtime")`，与「该组合下 runtime 真实最优」的一行对比；若推荐策略与 partition 数与真实最优一致，则计为一致。
- **脚本**：`advisor/scripts/evaluate_advisor.py`。
- **运行**（项目根目录）：`python3 advisor/scripts/evaluate_advisor.py`

### 5.2 评估结果（objective=runtime）

在 `advisor/experiment_summary.csv` 当前数据下运行上述脚本，得到：

| data_size | query_type | Advisor 推荐 | 真实最优 | 一致 |
|-----------|------------|--------------|----------|------|
| 500mb | aggregate | spark_repartition n=4 | spark_repartition n=4 | 是 |
| 500mb | join | spark_repartition n=16 | spark_repartition n=16 | 是 |
| 500mb | window | hive | hive | 是 |
| 50mb | aggregate | spark_repartition n=4 | spark_repartition n=4 | 是 |
| 50mb | join | spark_repartition n=4 | spark_repartition n=4 | 是 |
| 50mb | window | spark_repartition n=16 | spark_repartition n=16 | 是 |
| 5gb | aggregate | hive | hive | 是 |
| 5gb | join | hive | hive | 是 |
| 5gb | window | hive | hive | 是 |
| 5mb | aggregate | spark_repartition n=32 | spark_repartition n=32 | 是 |
| 5mb | join | spark_repartition n=4 | spark_repartition n=4 | 是 |
| 5mb | window | spark_repartition n=4 | spark_repartition n=4 | 是 |

**一致率：12/12 = 100.0%**

（即：在现有实验组合上，Advisor 的推荐与汇总表中 runtime 最优配置完全一致；可直接用于报告/论文的评估部分。）

---

## 6. 局限与未来工作

- **当前局限**：单集群、三类查询（aggregate/join/window）、固定 schema；推荐完全依赖现有实验汇总表，未使用 SQL 解析或实时集群状态。
- **未来工作**：可考虑（1）用 experiment_summary 训练简单模型（如决策树/随机森林）作为 V2，对比规则与模型推荐一致率；（2）增加配置维度（如 spark.sql.shuffle.partitions、更多 repartition 数）；（3）倾斜感知或更多查询类型与数据规模。
