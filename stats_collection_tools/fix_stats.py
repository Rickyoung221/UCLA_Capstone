"""
Docker Stats Data Fix Script

Fixes statistical errors in Docker stats CSV files:
1. Memory usage: Corrects total memory calculation in ALL rows
2. Memory percentage: Fixes percentage calculation based on actual container usage
3. Network IO: Adds missing network IO totals in ALL rows
4. Units: Standardizes memory (binary) and network (decimal) units

Example fix:
Before:
TimeStamp,Container,Name,CPUPerc,MemUsage,MemPerc,NetIO,BlockIO,PIDs
2025-03-12 00:27:12,ALL,All Containers,4.53%,1,089.35 MB,5.71%,0 MB / 0 MB,0 MB / 0 MB,989

After:
TimeStamp,Container,Name,CPUPerc,MemUsage,MemPerc,NetIO,BlockIO,PIDs
2025-03-12 00:27:12,ALL,All Containers,4.53%,6.70GiB / 23.47GiB,28.54%,1.42GB / 1.42GB,0B / 0B,989
"""

import pandas as pd
import re
import os
import glob

def convert_memory_to_bytes(mem_str):
    """
    Convert memory string to bytes
    Input format: '1.754GiB', '1022MiB'
    Uses binary units (1024-based) for memory
    """
    if isinstance(mem_str, str) and '/' in mem_str:
        mem_str = mem_str.split('/')[0].strip()
    
    match = re.match(r'([\d.]+)\s*([GMK])?iB', str(mem_str))
    if not match:
        return 0
    
    num, unit = match.groups()
    num = float(num)
    if unit == 'G':
        return num * 1024 * 1024 * 1024  # GiB to bytes
    elif unit == 'M':
        return num * 1024 * 1024         # MiB to bytes
    elif unit == 'K':
        return num * 1024                # KiB to bytes
    return num

def convert_network_to_bytes(net_str):
    """
    Convert network IO string to bytes
    Input format: '687MB', '14.2MB'
    Uses decimal units (1000-based) for network
    """
    if not isinstance(net_str, str):
        return 0
        
    match = re.match(r'([\d.]+)\s*([GMK])?B', net_str.strip())
    if not match:
        return 0
        
    num, unit = match.groups()
    num = float(num)
    if unit == 'G':
        return num * 1000 * 1000 * 1000  # GB to bytes
    elif unit == 'M':
        return num * 1000 * 1000         # MB to bytes
    elif unit == 'K':
        return num * 1000                # KB to bytes
    return num

def convert_bytes_to_readable(bytes_val, use_binary=False):
    """
    Convert bytes to human readable format
    use_binary=True: KiB, MiB, GiB (1024-based) for memory
    use_binary=False: KB, MB, GB (1000-based) for network
    """
    if use_binary:
        units = ['B', 'KiB', 'MiB', 'GiB']
        divisor = 1024.0
    else:
        units = ['B', 'KB', 'MB', 'GB']
        divisor = 1000.0
        
    bytes_val_copy = bytes_val
    for unit in units:
        if bytes_val_copy < divisor:
            return f"{bytes_val_copy:.2f}{unit}"
        bytes_val_copy /= divisor
    return f"{bytes_val_copy:.2f}{units[-1]}"

def parse_network_io(io_str):
    """
    Parse network IO string
    Format: '14.2MB / 1.2MB'
    Returns: (input_bytes, output_bytes)
    """
    if isinstance(io_str, str):
        parts = io_str.split('/')
        if len(parts) == 2:
            return (convert_network_to_bytes(parts[0].strip()),
                   convert_network_to_bytes(parts[1].strip()))
    return (0, 0)

def fix_stats(input_file, output_file):
    """
    Fix stats for a single file
    - Keeps original CPU percentages
    - Corrects memory usage and percentages
    - Adds network IO totals
    - Standardizes units
    """
    print(f"Processing: {input_file}")
    df = pd.read_csv(input_file)
    
    timestamps = df['TimeStamp'].unique()
    fixed_rows = []
    
    for ts in timestamps:
        group = df[df['TimeStamp'] == ts]
        containers = group[group['Container'] != 'ALL']
        
        # Calculate totals
        total_cpu = containers['CPUPerc'].apply(lambda x: float(x.strip('%'))).sum()
        total_mem = containers['MemUsage'].apply(lambda x: convert_memory_to_bytes(x.split('/')[0])).sum()
        total_mem_str = f"{convert_bytes_to_readable(total_mem, use_binary=True)} / 23.47GiB"
        total_mem_perc = (total_mem / (23.47 * 1024 * 1024 * 1024)) * 100
        
        # Sum network IO
        net_io_in = net_io_out = 0
        for _, row in containers.iterrows():
            in_bytes, out_bytes = parse_network_io(row['NetIO'])
            net_io_in += in_bytes
            net_io_out += out_bytes
        
        total_net_io = f"{convert_bytes_to_readable(net_io_in)} / {convert_bytes_to_readable(net_io_out)}"
        total_pids = containers['PIDs'].astype(int).sum()
        
        # Keep original container rows
        fixed_rows.extend(containers.to_dict('records'))
        
        # Add fixed ALL row
        all_row = {
            'TimeStamp': ts,
            'Container': 'ALL',
            'Name': 'All Containers',
            'CPUPerc': f"{total_cpu:.2f}%",
            'MemUsage': total_mem_str,
            'MemPerc': f"{total_mem_perc:.2f}%",
            'NetIO': total_net_io,
            'BlockIO': '0B / 0B',
            'PIDs': str(total_pids)
        }
        fixed_rows.append(all_row)
    
    fixed_df = pd.DataFrame(fixed_rows)
    fixed_df.to_csv(output_file, index=False)
    print(f"Saved: {output_file}")

def process_all_stats():
    """
    Process all stats files in *mb_stats directories
    Creates a 'fixed' subdirectory in each stats directory
    Output files are prefixed with 'fixed-'
    """
    stats_dirs = glob.glob("*mb_stats")
    
    for stats_dir in stats_dirs:
        print(f"\nDirectory: {stats_dir}")
        csv_files = glob.glob(os.path.join(stats_dir, "*.csv"))
        
        fixed_dir = os.path.join(stats_dir, "fixed")
        os.makedirs(fixed_dir, exist_ok=True)
        
        for csv_file in csv_files:
            filename = os.path.basename(csv_file)
            output_file = os.path.join(fixed_dir, f"fixed-{filename}")
            fix_stats(csv_file, output_file)

if __name__ == "__main__":
    process_all_stats() 