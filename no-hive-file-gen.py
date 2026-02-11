import os
import re

# Define enumerated sizes and repartition values.
sizes = ["5mb", "50mb", "500mb"]
repartition_vals = [4, 16, 32]

# Map template file names to their corresponding task descriptions.
# task1 => Aggregate, task2 => Join, task3 => Window.
tasks = {
    "no-hive-task1.py": "Aggregate",
    "no-hive-task2.py": "Join",
    "no-hive-task3.py": "Window"
}

# Process each size folder.
for size in sizes:
    folder = size
    os.makedirs(folder, exist_ok=True)
    
    # Process each template file.
    for template_file, task_desc in tasks.items():
        # Read the template file.
        with open(template_file, "r") as f:
            content = f.read()
        
        # Replace the CSV path: change "5mb" in the path to the current size.
        # For example: hdfs://master:8020/data/5mb.csv -> hdfs://master:8020/data/50mb.csv
        content = content.replace("hdfs://master:8020/data/5mb.csv", f"hdfs://master:8020/data/{size}.csv")
        
        # For each repartition value, generate a new file.
        for repart in repartition_vals:
            new_content = content
            
            # Replace the repartition call: replace the number in df.repartition(10) with the current repartition value.
            new_content = re.sub(r'df\s*=\s*df\.repartition\(\s*\d+\s*\)', 
                                 f"df = df.repartition({repart})", 
                                 new_content)
            
            # Update the Spark application name.
            # Original line: .appName("TestWithoutHiveNYC1")
            # New name: e.g. Test5MB_Aggregate_4 for no-hive-task1.py with size 5mb and repartition 4.
            new_app_name = f"Test{size.upper()}_{task_desc}_{repart}"
            new_content = re.sub(r'\.appName\(".*?"\)', 
                                 f'.appName("{new_app_name}")', 
                                 new_content)
            
            # Construct the new file name.
            base = os.path.splitext(template_file)[0]
            new_file_name = f"{base}_{repart}.py"
            new_file_path = os.path.join(folder, new_file_name)
            
            # Write the modified content to the new file.
            with open(new_file_path, "w") as f:
                f.write(new_content)
            
            print(f"Generated {new_file_path}")
