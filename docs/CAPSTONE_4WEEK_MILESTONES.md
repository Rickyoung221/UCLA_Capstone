# Capstone 四周 Milestone

基于 [CAPSTONE_EXTENSION_IDEAS.md](CAPSTONE_EXTENSION_IDEAS.md) 的 Workload-Aware Partitioning Advisor 延伸，按周拆解可交付成果与检查点。

---

## 总览

| 周次 | 主题 | 核心交付 |
|------|------|----------|
| Week 1 | 数据与实验汇总 | 统一实验表 + 脚本 + 文档 |
| Week 2 | Advisor V1（规则/查表） | `recommend()` + CLI |
| Week 3 | 评估与展示 | 评估方法 + 简单 Web 或报告用图 |
| Week 4 | 收尾与可选扩展 | 文档/README + 可选 ML 或配置扩展 |

---

## Week 1：数据与实验汇总

**目标**：把现有实验结果整理成一张可被 Advisor 和报告复用的“实验汇总表”，并写好生成脚本与文档。

### 任务清单

- [ ] **1.1** 设计并确定汇总表 schema  
  - 列至少包含：`data_size`, `query_type`, `strategy`, `num_partitions`（若适用）, `runtime_seconds`, `max_cpu`, `max_memory_mib`  
  - 若已有列名不统一，在 schema 里定好标准命名（如 `aggregate`/`join`/`window`，`hive`/`spark_repartition_4` 等）

- [ ] **1.2** 编写汇总脚本（如 `stats_collection_tools/merge_experiment_results.py` 或 `advisor/scripts/build_summary.py`）  
  - 输入：现有 `*_results.csv`、各 `*_stats` 目录下的 CSV、`resource_usage_summary.csv` 等  
  - 输出：单张 CSV，例如 `advisor/experiment_summary.csv`（或项目根目录下的 `experiment_summary.csv`）

- [ ] **1.3** 跑通脚本并生成第一版 `experiment_summary.csv`  
  - 检查覆盖：所有 data size × query type × strategy 组合是否都有记录（缺的可在文档中标明“待补跑”）

- [ ] **1.4** 在 `docs/` 下写 **实验设计** 短文（如 `docs/EXPERIMENT_DESIGN.md`）  
  - 数据规模、查询类型、策略与配置组合、指标含义、如何复现（如何跑任务、如何收集 runtime/资源）

### Week 1 完成标准

- 存在一张 `experiment_summary.csv`，且 schema 文档化  
- 存在可复现的汇总脚本，README 或 docs 中说明如何生成该表  
- 实验设计文档能支撑后续“方法”与“实验”章节的写作  

---

## Week 2：Advisor V1（规则 + 查表）

**目标**：实现基于汇总表的推荐逻辑与 CLI，完成“输入 workload → 输出策略与配置”的闭环。

### 任务清单

- [ ] **2.1** 在仓库中建立 `advisor/` 目录（若尚未建立）  
  - 至少包含：`recommend.py`（或等价模块）、`README.md` 说明输入/输出与用法

- [ ] **2.2** 实现 `recommend(data_size, query_type, objective='runtime'?)`  
  - 读取 `experiment_summary.csv`  
  - 对给定 `(data_size, query_type)` 筛选记录，按 `objective`（如 runtime 最小或 CPU/内存加权）选最优一行  
  - 返回：推荐策略（如 `hive` 或 `spark_repartition`）、推荐 partition 数（若适用）、以及简短理由（如 “lowest runtime in 50mb join experiments”）

- [ ] **2.3** 实现 CLI 入口（如 `advisor/advisor.py` 或 `advisor/cli.py`）  
  - 示例：`python advisor/advisor.py --data-size 50mb --query-type join`  
  - 输出：推荐策略、推荐配置、理由（可加 `--objective runtime|cpu|memory` 等）

- [ ] **2.4** 在 `advisor/README.md` 中写清：  
  - 输入（data_size、query_type、可选 objective）  
  - 输出（strategy、num_partitions、reason）  
  - 依赖（experiment_summary.csv 的路径与生成方式）

### Week 2 完成标准

- 对任意已出现在汇总表中的 `(data_size, query_type)`，CLI 能给出明确推荐与理由  
- 他人按 README 可复现：生成汇总表 → 运行 advisor 得到推荐  

---

## Week 3：评估与展示

**目标**：定义并实现一种“Advisor 是否靠谱”的评估方式，并做好结果展示（图或简单界面），便于写进报告/论文。

### 任务清单

- [ ] **3.1** 确定评估方式（二选一或都做）  
  - **方式 A**：在现有汇总表上，对比“Advisor 推荐”与“该组合下真实最优”的一致率（即推荐是否等于 runtime 最优策略）  
  - **方式 B**：选 1～2 个未参与汇总的 data size 或 query 变体，实际跑一遍实验，再对比“按 Advisor 推荐跑” vs “其他策略”的 runtime/资源

- [ ] **3.2** 实现评估脚本或 notebook  
  - 若选方式 A：脚本读汇总表，对每个 `(data_size, query_type)` 调用 `recommend()`，与真实最优比较，输出一致率或混淆表  
  - 若选方式 B：在文档中写明补跑步骤，并记录结果到 CSV 或 Markdown 表

- [ ] **3.3** 做 1～2 张可用于报告/论文的图  
  - 例如：不同 (data_size, query_type) 下 Hive vs Spark repartition 的 runtime 对比柱状图；或 Advisor 推荐 vs 实际最优的对比表/图

- [ ] **3.4**（可选）简单 Web 展示  
  - 下拉选择 data size、query type，展示推荐结果 + 理由；可附链接到现有 `*mb.html` 等可视化  
  - 若时间紧可改为“在 README 中贴 CLI 示例输出 + 一张结果表”

### Week 3 完成标准

- 有明确的“如何评估 Advisor”的说明与（至少一种）可复现结果  
- 至少有 1 张图或 1 张表可直接用于报告/论文的“实验/评估”部分  

---

## Week 4：收尾与可选扩展

**目标**：补齐文档、与主项目 README 集成，并视时间做一项可选扩展（ML 模型或配置维度）。

### 任务清单

- [ ] **4.1** 文档收尾  
  - **Advisor 设计**：在 `docs/` 下写 `ADVISOR_DESIGN.md`（或扩写 CAPSTONE_EXTENSION_IDEAS），说明输入/输出、规则逻辑、依赖的数据与表结构  
  - **README**：在主项目 `README.md` 中增加 “Capstone: Partitioning Advisor” 一节，说明如何生成汇总表、如何运行 Advisor、如何复现评估

- [ ] **4.2** 代码与路径整理  
  - 确保 `advisor/` 下脚本可被清晰调用（如统一用 `python -m advisor.advisor` 或根目录 `python advisor/advisor.py`）  
  - 若汇总表路径可配置（如环境变量或 config），在 README 中说明

- [ ] **4.3** 可选扩展（时间允许则选做其一）  
  - **选项 A**：Advisor V2 — 用 `experiment_summary.csv` 训练简单决策树/随机森林，特征为 data_size + query_type 编码，目标为 best strategy 或 runtime；对比“规则查表 vs 模型”的推荐一致率  
  - **选项 B**：配置扩展 — 在 1～2 个 no-hive 任务上增加不同 `spark.sql.shuffle.partitions` 或 repartition 数实验，将结果并入汇总表，并让 Advisor 在推荐时考虑这些配置

- [ ] **4.4** 未来工作与局限性  
  - 在 `docs/` 或报告里写一段：当前仅限单集群、三类查询、给定 schema；未来可做倾斜感知、更多配置维度、更多查询类型等  

### Week 4 完成标准

- 主 README 与 `docs/` 能支撑他人理解并复现整个 Capstone 延伸  
- 若做了可选扩展，有对应小节说明与结果；若未做，有清晰的“未来工作”描述  

---

## 检查表（按周自检）

| 周 | 可交付 | 完成 |
|----|--------|------|
| 1 | `experiment_summary.csv` + 汇总脚本 + 实验设计文档 | ☐ |
| 2 | `recommend()` + CLI + `advisor/README.md` | ☐ |
| 3 | 评估方式 + 评估结果/脚本 + 至少 1 张报告用图或表 | ☐ |
| 4 | Advisor 设计文档 + 主 README 更新 + 可选扩展或未来工作 | ☐ |

---

## 若进度落后可做的裁剪

- **Week 3**：不做 Web，只做“推荐 vs 真实最优”一致率表格 + 一张图。  
- **Week 4**：不做 ML 与配置扩展，只做文档与 README，把 V2/配置扩展写进“未来工作”。  
- 倾斜感知、更多 Spark 参数：整项放在“未来工作”，不纳入四周必做范围。

这样四周后可以交付：**可复现的实验汇总、可用的规则型 Advisor、可写进报告的评估与图、以及完整文档与可选扩展**。
