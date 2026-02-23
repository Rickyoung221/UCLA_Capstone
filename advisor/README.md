# Partitioning Advisor（Capstone）

轻量级、workload-aware 的 partitioning 建议器：根据 **数据规模** 与 **查询类型** 推荐使用 **Hive 分区** 还是 **Spark repartition**，以及推荐的 partition 数量。

---

## 数据依赖

Advisor 的推荐基于 **实验汇总表** `experiment_summary.csv`，该表由以下脚本从现有实验结果生成：

```bash
# 在项目根目录执行
python3 advisor/scripts/build_summary.py
```

- **输入**：`stats_collection_tools/` 下的 `*_results.csv` 与 `*_stats/*.csv`。
- **输出**：`advisor/experiment_summary.csv`（见 [实验设计](../docs/EXPERIMENT_DESIGN.md)）。

若尚未生成，请先运行上述命令。

---

## 使用方式

### CLI（推荐）

在项目根目录执行：

```bash
python3 advisor/advisor.py --data-size 50mb --query-type join
python3 advisor/advisor.py -s 5mb -q window --objective runtime
python3 advisor/advisor.py -s 500mb -q aggregate -v   # -v 打印 runtime/cpu/memory 详情
```

- `--data-size` / `-s`：数据规模，如 5mb、50mb、500mb。
- `--query-type` / `-q`：查询类型，aggregate / join / window。
- `--objective` / `-o`：优化目标，runtime（默认）/ cpu / memory（后两者在无资源数据时回退为 runtime）。

### 在代码中调用

```python
from recommend import recommend

strategy, num_partitions, reason, row = recommend("50mb", "join")
# strategy == "spark_repartition", num_partitions == 4, reason 为说明字符串
```

---

## 目录结构

```
advisor/
├── README.md                 # 本说明
├── experiment_summary.csv    # 统一实验汇总表（由 scripts/build_summary.py 生成）
├── recommend.py              # 推荐逻辑 recommend(data_size, query_type, objective=...)
├── advisor.py                # CLI 入口
└── scripts/
    ├── build_summary.py      # 汇总脚本：合并 runtime + 资源指标 → experiment_summary.csv
    ├── evaluate_advisor.py   # 评估脚本：推荐 vs 真实最优、一致率
    └── plot_runtime.py       # 画 runtime 对比图（需 matplotlib）
```

---

## 汇总表 Schema（简要）

| 列              | 说明                                    |
| --------------- | --------------------------------------- |
| data_size       | 5mb / 50mb / 500mb                      |
| query_type      | aggregate / join / window               |
| strategy        | hive / spark_repartition                |
| num_partitions  | 4 / 16 / 32（仅 spark_repartition）或空 |
| runtime_seconds | 最小运行时间（秒）                      |
| max_cpu_pct     | 最大 CPU 使用率（%）                    |
| max_memory_mib  | 最大内存（MiB）                         |

详见 [docs/EXPERIMENT_DESIGN.md](../docs/EXPERIMENT_DESIGN.md)。
