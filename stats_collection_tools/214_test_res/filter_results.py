import pandas as pd

file_name = './join_cleaned_results'

# Load the CSV data
df = pd.read_csv(f"{file_name}.csv")

# Define the allowed ending numbers as strings
lst = [54, 55, 56, 57, 58, 59, 60, 61]
allowed_endings = [str(n) for n in lst]  # This creates ['6', '7', ..., '18']

# Filter the DataFrame:
# This assumes the column containing the id is named 'application id'.
# If the column name is different, adjust accordingly.
filtered_df = df[df['id'].astype(str).str.endswith(tuple(allowed_endings))]

# Optionally, save the filtered data to a new CSV file
filtered_df.to_csv(f"{file_name}_filtered.csv", index=False)

print(f"Filtered data saved to {file_name}_filtered.csv")
