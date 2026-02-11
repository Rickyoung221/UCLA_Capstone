# 资源使用统计分析工具

本项目包含一系列用于分析和可视化Docker容器资源使用情况的Python脚本。

## 数据说明

所有带有`_stats`后缀的目录中的CSV文件已经过修复和清理，可以直接使用。包括：
- `5mb_stats/`
- `50mb_stats/`
- `500mb_stats/`
- `join_stats/`

## 脚本说明

### 1. process_stats.py
用于处理统计数据，提取每个任务的最大CPU和内存使用情况。

使用方法：
```bash
python3 process_stats.py
```
输出：生成 `max_resource_usage.csv` 文件，包含所有任务的最大资源使用情况。

### 2. visualize_stats.py
用于生成资源使用情况的可视化图表。

使用方法：
```bash
python3 visualize_stats.py
```
输出：
- `resource_usage_comparison.png`：包含CPU使用率和内存使用量的对比图表
- `resource_usage_summary.csv`：包含各数据集的资源使用统计汇总

## 依赖安装

项目依赖已在 `requirements.txt` 中列出，可通过以下命令安装：
```bash
python3 -m pip install -r requirements.txt
```

## 主要依赖
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0

## 注意事项
1. 图表生成时需要支持中文字体显示
2. 统计结果包含了每个数据集（5MB、50MB、500MB和join操作）的资源使用情况
3. 所有结果都已经过清理和标准化处理 