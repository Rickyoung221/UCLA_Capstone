"""
此脚本用于处理HTML文件中的Spark应用程序运行数据。
主要功能：
1. 解析HTML文件中的表格数据
2. 提取应用程序ID、名称和运行时间信息
3. 清理和过滤数据
4. 生成统计报告和CSV文件
"""

from bs4 import BeautifulSoup
import pandas as pd
import os
import re
from datetime import datetime

def parse_time(time_str):
    """
    解析时间字符串为datetime对象
    
    参数:
        time_str: 包含时间信息的字符串，格式如 "Wed Mar 12 17:56:43 +0800 2025"
        
    返回:
        datetime对象 或 None（如果解析失败）
    """
    try:
        # 处理 N/A 情况
        if time_str == 'N/A':
            return None
            
        # 从字符串中提取时间部分
        time_match = re.search(r'(\d{2}:\d{2}:\d{2})', time_str)
        date_match = re.search(r'(Mar \d{2})', time_str)
        
        if time_match and date_match:
            # 组合日期和时间
            dt_str = f"{date_match.group(1)} 2025 {time_match.group(1)}"
            dt = datetime.strptime(dt_str, '%b %d %Y %H:%M:%S')
            return dt
        return None
    except Exception as e:
        print(f"Error parsing time: {time_str} - {e}")
        return None

def calculate_duration(start, finish):
    """
    计算两个时间点之间的持续时间
    
    参数:
        start: 开始时间（datetime对象）
        finish: 结束时间（datetime对象）
        
    返回:
        持续时间（秒），如果输入无效则返回None
    """
    if start and finish:
        duration = finish - start
        return duration.total_seconds()
    return None

def clean_name(name):
    """
    清理和标准化名称字符串
    
    参数:
        name: 原始名称字符串
        
    返回:
        清理后的名称字符串
    """
    # 统一名称格式
    name = name.strip()
    # 移除多余的空格
    name = re.sub(r'\s+', ' ', name)
    return name

def process_html_file(file_path):
    """
    处理单个HTML文件，提取并清理数据
    
    参数:
        file_path: HTML文件路径
        
    返回:
        包含清理后数据的DataFrame对象
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        
        records = []
        # 查找所有行
        rows = soup.find_all('tr', role='row')
        
        # 遍历每一行提取数据
        for row in rows:
            try:
                # 获取所有单元格
                cells = row.find_all('td')
                if len(cells) < 10:  # 跳过标题行
                    continue
                    
                # 提取数据
                app_id = cells[0].get_text(strip=True)
                name = clean_name(cells[2].get_text(strip=True))
                start_time_str = cells[7].get_text(strip=True)
                launch_time_str = cells[8].get_text(strip=True)
                finish_time_str = cells[9].get_text(strip=True)
                
                # 解析时间
                start_time = parse_time(start_time_str)
                launch_time = parse_time(launch_time_str)
                finish_time = parse_time(finish_time_str)
                
                # 计算运行时间（秒）
                runtime = calculate_duration(start_time, finish_time)
                    
                # 将提取的数据添加到记录列表
                records.append({
                    'id': app_id,
                    'name': name,
                    'start_time': start_time_str,
                    'launch_time': launch_time_str,
                    'finish_time': finish_time_str,
                    'runtime_seconds': runtime
                })
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
            
        # 创建DataFrame
        df = pd.DataFrame(records)
        
        if not df.empty:
            # 数据清理过程
            print("\n原始数据统计：")
            print(f"记录总数: {len(df)}")
            
            # 1. 移除运行时间为空的记录
            df = df.dropna(subset=['runtime_seconds'])
            print(f"移除运行时间为空后的记录数: {len(df)}")
            
            # 2. 移除运行时间异常的记录（例如小于5秒或大于300秒）
            df = df[df['runtime_seconds'].between(5, 300)]
            print(f"移除运行时间异常后的记录数: {len(df)}")
            
            # 3. 移除重复记录
            df = df.drop_duplicates(subset=['name', 'runtime_seconds'])
            print(f"移除重复记录后的记录数: {len(df)}")
            
            # 4. 按名称和运行时间排序
            df = df.sort_values(['name', 'runtime_seconds'])
            
        return df

def main():
    """
    主函数：处理所有HTML文件并生成报告
    """
    # 处理所有HTML文件
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    for html_file in html_files:
        print(f"\nProcessing {html_file}...")
        df = process_html_file(html_file)
        
        if df is not None and not df.empty:
            # 生成输出文件名
            output_file = f"{os.path.splitext(html_file)[0]}_cleaned_results.csv"
            df.to_csv(output_file, index=False)
            print(f"\nResults saved to {output_file}")
            
            # 显示数据统计
            print("\n清理后的数据统计：")
            # 按名称分组计算统计信息
            stats = df.groupby('name')['runtime_seconds'].agg(['count', 'mean', 'min', 'max'])
            print(stats)
            
            # 显示前几行数据
            print("\n清理后的前几行数据：")
            print(df[['name', 'runtime_seconds']].head())

if __name__ == "__main__":
    main() 