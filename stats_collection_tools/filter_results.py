import os

current_directory = os.getcwd()
print("Current working directory:", current_directory)

import pandas as pd

file_name = './5mb_cleaned_results'

# Load the CSV data
df = pd.read_csv(f"{file_name}.csv")

# Define the allowed ending numbers as strings
allowed_endings = [str(n) for n in range(6, 19)]  # This creates ['6', '7', ..., '18']

# Filter the DataFrame:
# This assumes the column containing the id is named 'application id'.
# If the column name is different, adjust accordingly.
filtered_df = df[df['application id'].astype(str).str.endswith(tuple(allowed_endings))]

# Optionally, save the filtered data to a new CSV file
filtered_df.to_csv("f{file_name}_filtered.csv", index=False)

print("Filtered data saved to f{file_name}_filtered.csv")
