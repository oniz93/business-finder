
import pandas as pd
import sys

# Simple script to read and inspect a Parquet file.

if len(sys.argv) < 2:
    print("Usage: python3 inspect_parquet.py <path_to_parquet_file>")
    sys.exit(1)

file_path = sys.argv[1]

df = pd.read_parquet(file_path)

print(f"--- Inspecting file: {file_path} ---")
print(f"Shape: {df.shape}")
print("\n--- Schema ---")
df.info()
print("\n--- First 2 Rows ---")
# Print the dataframe as markdown for better readability
print(df.head(2).to_markdown(index=False))
