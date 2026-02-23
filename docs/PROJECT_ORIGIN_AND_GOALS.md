# 项目来源与 Capstone 目标

## 1. 项目来源：CS 214 课程项目

本 Capstone 基于 **CS 214 课程项目** 中的系统实验/benchmark：

- **环境**：Spark–Hive 集群（本仓库使用 Docker 部署 Hadoop + Hive + Spark）。
- **实验内容**：
  - 对比 **Hive 原生 partitioning** 与 **Spark 显式 repartition** 两种策略。
  - 覆盖不同 **数据规模**（如 5MB / 50MB / 500MB）与不同 **查询类型**：
    - aggregation（聚合）
    - join（连接）
    - window functions（窗口函数）
  - **指标**：以 runtime、资源使用（CPU/内存）等性能与资源权衡为主。

课程项目已完成的实验与数据收集流程见 [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md)。

---

## 2. Capstone 核心：从“堆实验”到可交付系统

Capstone 的延伸方向**不是继续堆更多实验**，而是做一个**小而可交付的系统型项目**：

### 2.1 目标

做一个 **轻量级、考虑工作负载（workload-aware）的「分区策略推荐/顾问（Advisor）」**。

### 2.2 输入（当前与可扩展）

- **当前已支持**：
  - 查询特征：查询类型（aggregation / join / window）。
  - 数据规模（如 5mb、50mb、500mb）。
- **可扩展**：SQL/query pattern、过滤条件、更多 workload 特征等。

### 2.3 输出

- 推荐策略：**该用 Hive partition 还是 Spark repartition**。
- 配置建议：例如 Spark repartition 时的 **partition 数量**（4 / 16 / 32 等）。
- 可选：优化目标（runtime / cpu / memory）下的说明或置信度。

### 2.4 价值

在给定 workload 下，**自动给出更合适的分区/重分区建议**，减少人工调参和试错。

---

## 3. 教授反馈

- 将课程项目延伸为 Capstone **很常见**，方向合理。
- **认可本方向**：“build a lightweight, workload-aware advisor”。
- **进一步建议**：可以**训练一个模型**来辅助完成推荐任务（例如用历史实验数据学习 (data_size, query_type, …) → 最优策略/配置）。

---

## 4. 与当前实现的对应关系

| 概念               | 当前实现                                                              |
| ------------------ | --------------------------------------------------------------------- |
| 输入：数据规模     | `advisor.py --data-size 5mb\|50mb\|500mb`                             |
| 输入：查询类型     | `--query-type aggregate\|join\|window`                                |
| 输入：优化目标     | `--objective runtime\|cpu\|memory`                                    |
| 输出：策略         | `recommend()` 返回 `hive` 或 `spark_repartition`                      |
| 输出：partition 数 | `num_partitions`：4 / 16 / 32（仅 spark_repartition）                 |
| 推荐依据           | 基于 `experiment_summary.csv` 的规则型选择（如按 objective 取最优行） |

后续可在此基础上增加：

- 更细的 query 特征（如 join 键数量、过滤选择性）。
- 基于历史数据训练的**模型**，用于预测策略或 partition 数，与现有规则形成混合推荐。
