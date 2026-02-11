import os
import re

# Define the sizes and the task mapping
sizes = ["5mb", "50mb", "500mb"]
# Mapping from template filename to a descriptive task name
tasks = {
    "hive-task1.py": "Aggregate",
    "hive-task2.py": "Join",
    "hive-task3.py": "Window"
}

# Process each size folder
for size in sizes:
    # Create folder if it does not exist
    folder = size
    os.makedirs(folder, exist_ok=True)
    
    for template_file, task_desc in tasks.items():
        # Read the template file
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Replace the table name in the SQL query.
        # All occurrences of 'taxi_data_partitioned_csv_5mb' will be replaced by the appropriate size.
        new_table_name = f"taxi_data_partitioned_csv_{size}"
        content = content.replace("taxi_data_partitioned_csv_5mb", new_table_name)
        
        # Update the Spark application name.
        # We search for .appName("...") and replace whatever is in the quotes with our new name.
        # New app name is constructed based on the size (in uppercase) and the task description.
        new_app_name = f"Test{size.upper()}_{task_desc}"
        content = re.sub(r'\.appName\(".*?"\)', f'.appName("{new_app_name}")', content)
        
        # Write the modified content to the appropriate folder, preserving the original filename.
        new_filename = os.path.join(folder, template_file)
        with open(new_filename, 'w') as f:
            f.write(content)
        
        print(f"Generated {new_filename}")
