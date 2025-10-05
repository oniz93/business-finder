import argparse
import os
import glob
import pandas as pd

def dump_spark_csv(input_dir: str, output_file: str):
    """
    Reads all .csv part-files from a Spark output directory,
    concatenates them, and saves them to a single CSV file.
    """
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory not found at '{input_dir}'")
        return

    # Spark CSV output directories contain part-files like part-00000-....csv
    csv_files = glob.glob(os.path.join(input_dir, "part-*.csv"))

    if not csv_files:
        print(f"Error: No CSV part-files found in '{input_dir}'")
        return

    print(f"Found {len(csv_files)} part-files to merge.")

    # Read all part-files into a list of DataFrames
    df_list = [pd.read_csv(f) for f in csv_files]

    # Concatenate all DataFrames
    combined_df = pd.concat(df_list, ignore_index=True)

    # Save to a single CSV file
    try:
        combined_df.to_csv(output_file, index=False)
        print(f"Successfully merged {len(combined_df)} rows into '{output_file}'")
    except Exception as e:
        print(f"Error saving the output file: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="A utility to merge partitioned CSV files from a Spark output directory into a single CSV file."
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the input directory containing Spark's partitioned CSV files (e.g., '.../cluster_assignments.csv_spark')."
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path for the single output CSV file."
    )
    args = parser.parse_args()

    dump_spark_csv(args.input, args.output)

if __name__ == "__main__":
    main()
