# 实验设计（Capstone 实验汇总表数据来源）

本文档说明 **experiment_summary.csv** 的数据来源、指标含义与复现方法，供 Advisor 与报告使用。

---

## 1. 汇总表 Schema

| 列名 | 含义 |
|------|------|
| `data_size` | 数据规模：5mb / 50mb / 500mb |
| `query_type` | 查询类型：aggregate / join / window |
| `strategy` | 分区策略：hive（Hive 原生分区）或 spark_repartition（Spark 显式 repartition） |
| `num_partitions` | 仅当 strategy=spark_repartition 时有值：4 / 16 / 32；Hive 时为空 |
| `runtime_seconds` | 该组合下多次运行中的 **最小** 运行时间（秒） |
| `max_cpu_pct` | 该任务运行期间容器最大 CPU 使用率（%），来自 *_stats 采样 |
| `max_memory_mib` | 该任务运行期间容器最大内存使用量（MiB），来自 *_stats 采样 |

---

## 2. 数据来源

### 2.1 运行时间（runtime_seconds）

- **来源**：`stats_collection_tools/` 下的 `5mb_results.csv`、`50mb_results.csv`、`500mb_results.csv`。
- **原始列**：每条记录包含 `name`（如 `Test50MB_Join_16`）、`runtime_seconds`。
- **解析规则**：
  - `Test{size}MB_{Aggregate|Join|Window}` → data_size={size}mb, query_type=aggregate|join|window, strategy=hive, num_partitions=空。
  - `Test{size}MB_{Aggregate|Join|Window}_{N}` → 同上，但 strategy=spark_repartition, num_partitions=N（4/16/32）。
- **聚合**：同一 (data_size, query_type, strategy, num_partitions) 可能有多条运行记录，汇总时取 **最小** runtime_seconds，作为该组合的“最佳运行时间”。

### 2.2 资源使用（max_cpu_pct, max_memory_mib）

- **来源**：`stats_collection_tools/{5mb,50mb,500mb}_stats/` 下的 CSV（如 `50mb-hive-task-1.csv`、`50mb-no-hive-task-2-16.csv`）。
- **命名规则**：
  - `{size}-hive-task-{1|2|3}.csv` → data_size={size}, query_type=aggregate|join|window（1→aggregate, 2→join, 3→window）, strategy=hive。
  - `{size}-no-hive-task-{1|2|3}-{N}.csv` → 同上，strategy=spark_repartition, num_partitions=N。
- **指标计算**：对每个 CSV，过滤掉 Container=ALL 的行，取所有时间点中 CPUPerc 最大值、MemUsage 最大值（统一换算为 MiB）。若某组合无对应 stats 文件，则 max_cpu_pct / max_memory_mib 为空。

---

## 3. 实验组合与复现

- **数据规模**：5mb、50mb、500mb（对应 HDFS 上的分区后表或 CSV 规模）。
- **查询类型**：
  - **aggregate**：GROUP BY 聚合（见 `aggregate.sql` / hive-task1 / no-hive-task1）。
  - **join**：多列等值+范围 JOIN（见 `join.sql` / hive-task2 / no-hive-task2）。
  - **window**：窗口函数 ROW_NUMBER / SUM OVER（见 `window.sql` / hive-task3 / no-hive-task3）。
- **策略**：
  - **hive**：使用 Hive 分区表，Spark 读 Hive 表执行 SQL。
  - **spark_repartition**：从 HDFS 读 CSV，`df.repartition(N)` 后建 temp view 再执行相同 SQL；N=4/16/32。

复现时：在 Docker 集群中按 `hive-file-gen.py` / `no-hive-file-gen.py` 生成任务并跑完，从 YARN/Spark History 收集应用名与 runtime，从 `docker stats` 或现有监控脚本采集各任务对应时间段的容器 CPU/内存，得到新的 *_results.csv 与 *_stats/*.csv，再运行汇总脚本即可更新 experiment_summary.csv。

---

## 4. 如何生成/更新 experiment_summary.csv

在项目根目录执行：

```bash
python3 advisor/scripts/build_summary.py
```

输出默认写入 `advisor/experiment_summary.csv`。可选参数：

- `--project-root <path>`：项目根目录（默认：脚本所在位置向上两级）。
- `-o <path>`：指定输出 CSV 路径。

脚本仅依赖 Python 3 标准库，无需安装 pandas。
