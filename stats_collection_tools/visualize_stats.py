import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 对于macOS
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('max_resource_usage.csv')

# 设置图表风格
sns.set_style("whitegrid")
plt.figure(figsize=(15, 10))

# 1. CPU使用率柱状图
plt.subplot(2, 1, 1)
sns.barplot(data=df, x='Dataset', y='Max_CPU_Usage', hue='Task')
plt.title('各任务最大CPU使用率对比')
plt.xlabel('数据集')
plt.ylabel('CPU使用率 (%)')
plt.xticks(rotation=45)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# 2. 内存使用量柱状图
plt.subplot(2, 1, 2)
sns.barplot(data=df, x='Dataset', y='Max_Memory_Usage_MiB', hue='Task')
plt.title('各任务最大内存使用量对比')
plt.xlabel('数据集')
plt.ylabel('内存使用量 (MiB)')
plt.xticks(rotation=45)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# 调整布局
plt.tight_layout()

# 保存图表
plt.savefig('resource_usage_comparison.png', bbox_inches='tight', dpi=300)
print("图表已保存为 resource_usage_comparison.png")

# 创建一个汇总统计表
summary = df.groupby('Dataset').agg({
    'Max_CPU_Usage': ['mean', 'max'],
    'Max_Memory_Usage_MiB': ['mean', 'max']
}).round(2)

# 重命名列
summary.columns = ['平均CPU使用率', '最大CPU使用率', '平均内存使用量(MiB)', '最大内存使用量(MiB)']

# 保存汇总统计
summary.to_csv('resource_usage_summary.csv')
print("汇总统计已保存为 resource_usage_summary.csv") 