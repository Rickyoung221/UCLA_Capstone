import os
import pandas as pd
import glob

def parse_memory(mem_str):
    if 'GiB' in mem_str:
        return float(mem_str.split('GiB')[0].strip()) * 1024
    elif 'MiB' in mem_str:
        return float(mem_str.split('MiB')[0].strip())
    return 0

def process_stats_files():
    # 存储所有结果
    all_results = []
    
    # 查找所有_stats目录
    stats_dirs = glob.glob('*_stats')
    
    for stats_dir in stats_dirs:
        # 获取基础名称（例如：从 "5mb_stats" 获取 "5mb"）
        base_name = stats_dir.replace('_stats', '')
        
        # 获取目录中的所有CSV文件
        csv_files = glob.glob(os.path.join(stats_dir, '*.csv'))
        
        for csv_file in csv_files:
            if 'fixed' in csv_file or os.path.basename(csv_file).startswith('fixed-'):
                continue
                
            try:
                # 读取CSV文件
                df = pd.read_csv(csv_file)
                
                # 过滤掉"ALL"行
                df = df[df['Container'] != 'ALL']
                
                # 获取最大CPU使用率
                max_cpu = df['CPUPerc'].str.rstrip('%').astype(float).max()
                
                # 获取最大内存使用量（MiB）
                df['MemValue'] = df['MemUsage'].apply(lambda x: parse_memory(x.split('/')[0].strip()))
                max_mem = df['MemValue'].max()
                
                # 获取任务名称
                task_name = os.path.basename(csv_file).replace('.csv', '')
                
                # 添加到结果列表
                all_results.append({
                    'Dataset': base_name,
                    'Task': task_name,
                    'Max_CPU_Usage': max_cpu,
                    'Max_Memory_Usage_MiB': max_mem
                })
                
            except Exception as e:
                print(f"处理文件 {csv_file} 时出错: {str(e)}")
    
    # 创建结果DataFrame
    results_df = pd.DataFrame(all_results)
    
    # 保存结果
    results_df.to_csv('max_resource_usage.csv', index=False)
    print("结果已保存到 max_resource_usage.csv")

if __name__ == "__main__":
    process_stats_files() 