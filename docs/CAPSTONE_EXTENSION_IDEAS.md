# Capstone 延伸方案：Workload-Aware Partitioning Advisor

## 1. 项目背景与毕设目标

- **CS214 已有工作**：在 Spark–Hive 环境中，对比 **Hive 原生分区** vs **Spark 显式 repartition**，在不同数据规模（5MB–5GB）、不同查询类型（aggregation / join / window）下的运行时间与资源消耗。
- **Capstone 目标**：做一个 **轻量级、workload-aware 的 advisor（建议器）**，根据：
  - **查询特征**：是否 join、是否 window、GROUP BY 结构等；
  - **数据特征**：表大小、分区数、倾斜情况等；  
  自动推荐 **partitioning 策略**（Hive partition vs Spark repartition）以及 **相关配置**（如 partition 数量、是否 coalesce 等）。

---

## 2. 难度评估：好做吗？和“理想形态”比如何？

### 结论：**难度适中，完全可做，且和你想的方向一致**

| 维度 | 说明 |
|------|------|
| **范围** | “轻量级 + workload-aware” 的定位很合适，不需要做通用优化器，只针对 partitioning 策略，范围清晰。 |
| **数据** | 你已有：多规模 × 多查询类型 × Hive/No-Hive × 多种 repartition 数，且有 runtime、CPU、内存等指标，**足够支撑规则或简单模型**。 |
| **实现路径** | 可先做 **规则/查表型 advisor**（基于现有 CSV 汇总），再视时间加 **简单 ML 或成本模型**，分阶段交付。 |
| **和“理想形态”比** | 理想形态可能是：任意 SQL + 任意集群 → 自动调优。你收敛到“查询类型 + 数据规模 → partitioning 策略 + 配置”，**更落地、可验证、易写进论文**，是合理的 capstone 范围。 |

**潜在难点（可控）**：

- **特征标准化**：把“查询特征”变成可用的输入（例如 SQL 解析出 join/window/group by），需要一点解析或约定（例如你已有三类 query 的标签）。
- **数据倾斜**：若要做“倾斜感知”，需要从 HDFS/Spark 拿分区大小或 task 耗时分布，工作量会上去一点，可以放在“未来工作”或简单指标（如分区数、总大小）。

---

## 3. 建议在现有项目上“加什么 / 改什么”

### 3.1 数据与特征层（为 advisor 提供输入）

- **统一实验指标表（推荐先做）**  
  - 把现有各 `*_results.csv`、`*_stats`、`resource_usage_summary.csv` 等汇总成 **一张表**，列包括至少：  
    `data_size, query_type (aggregate/join/window), strategy (hive | spark_repartition_N), runtime_seconds, max_cpu, max_memory_mib`。  
  - 便于：① 画对比图、写实验章节；② 作为 advisor 的“经验数据”或训练数据。

- **查询特征抽象**  
  - 当前已有三类：Aggregate、Join、Window。  
  - 可增加（可选）：  
    - `group_by_columns_count`；  
    - `join_type`（等值 / 范围）；  
    - `window_partition_by_columns_count`。  
  - 实现方式：要么在跑任务时写死标签，要么写一个 **简单的 SQL 解析**（正则或 `sqlparse`）从 `aggregate.sql` / `join.sql` / `window.sql` 里抽这些信息，供 advisor 使用。

- **数据特征（尽量复用现有）**  
  - 已有：数据规模（5mb / 50mb / 500mb / 5gb）、分区方式（Hive 分区数可从 partition 脚本得知）。  
  - 若有时间：加“倾斜度”指标（例如各 partition 行数或大小的方差），从 Spark UI 或 HDFS 统计脚本取一次即可，不必实时。

### 3.2 Advisor 核心：推荐逻辑

- **V1：规则 + 查表（最低可行）**  
  - 输入：`(data_size_bucket, query_type)`，例如 `("50mb", "join")`。  
  - 输出：在汇总表里查该组合下 **runtime 最短**（或 CPU/内存加权）的策略与配置，例如 `strategy=spark_repartition, num_partitions=16`。  
  - 实现：一个 Python 模块，读汇总 CSV，对外提供 `recommend(data_size, query_type) -> (strategy, num_partitions?)`。  
  - **这样就已经是“workload-aware advisor”**，且完全基于你现有实验数据。

- **V2：简单模型（加分项）**  
  - 用 `sklearn` 决策树或随机森林：特征 = `[data_size_mb, query_type_onehot, ...]`，目标 = `best_strategy` 或 `runtime`。  
  - 训练数据就是你汇总的实验表；可对比“规则查表 vs 模型”的推荐一致率或事后 runtime。

- **V3：配置扩展（若时间充裕）**  
  - “Configuration choices” 可具体化为：  
    - Spark：`spark.sql.shuffle.partitions`、`spark.default.parallelism`；  
    - 或是否在 no-hive 路径上先 `coalesce` 再 repartition。  
  - 在现有 no-hive 脚本里加一两组配置实验，把结果并入汇总表，advisor 即可推荐“策略 + 关键配置”。

### 3.3 工程与展示

- **Advisor 接口**  
  - CLI：`python advisor.py --data-size 50mb --query-type join` 输出推荐与简短理由。  
  - 或简单 Web：下拉选择 data size、query type，展示推荐 + 指向现有 50mb.html 等可视化链接。

- **文档与复现**  
  - `docs/` 下增加：  
    - **实验设计**：数据规模、查询类型、策略与配置组合、如何收集 runtime/资源；  
    - **Advisor 设计**：输入/输出、规则或模型版本、如何从现有 CSV 构建。  
  - README 中加一节 “Capstone: Partitioning Advisor”，说明如何跑实验、如何生成汇总表、如何运行 advisor。

### 3.4 论文/报告可写的点

- 对比实验：Hive vs Spark repartition 在不同规模、不同 query type 下的表现（你已有数据）。  
- Advisor 设计：workload-aware 的含义；输入（查询特征 + 数据特征）、输出（策略 + 配置）。  
- 评估：在“未参与训练”的规模或查询上（若有）看推荐是否仍优；或人工构造几条 SQL，用 advisor 推荐后实际跑一遍对比。  
- 局限性：单集群、固定 schema、三类查询；未来可扩展到更多配置与倾斜感知。

---

## 4. 建议的推进顺序（避免做难）

1. **先做**：统一实验指标表 + 规则/查表版 advisor（V1）+ CLI。  
2. **再做**：Advisor 的 README 与 `docs/` 说明；可选简单前端或 CLI 增强。  
3. **可选**：简单 ML 模型（V2）、或 1～2 个 configuration 维度（V3）。  
4. **若时间紧**：倾斜度可以只写“未来工作”，不实现。

这样你可以在 **不推翻现有 CS214 工作** 的前提下，把“对比实验”升级为“**基于实验数据的轻量级 workload-aware partitioning advisor**”，难度可控，且和你想的“根据查询特征 + 数据规模推荐策略与配置”完全一致。

---

## 5. 小结

- **难不难？** 不难到做不完，只要把范围锁在“轻量级 + partitioning 策略 + 可选配置”上。  
- **和你想的比？** 方向一致；把“configuration choices”具体化为 partition 数、少量 Spark 参数即可，不需要做通用 SQL 优化器。  
- **第一步建议**：建一张“实验汇总表”，实现一个基于该表的 **recommend(data_size, query_type)**，再围绕它写文档和简单界面，就已经是一个完整的 capstone 延伸。

如果你愿意，下一步可以在本仓库里加一个 `advisor/` 目录骨架（例如 `advisor/README.md`、`advisor/experiment_summary.csv` 的 schema、`advisor/recommend.py` 的接口约定），我可以按你当前 CSV 的格式帮你写一版示例实现。
