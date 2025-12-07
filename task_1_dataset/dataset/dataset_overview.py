import os
import pandas as pd

# Root folder of your dataset (change if needed)
ROOT_DIR = "."  # <-- replace with the actual path if different


def analyze_csv_files(root_path):
    print("Scanning for CSV files...\n")

    for folder, subfolders, files in os.walk(root_path):
        for file in files:
            if file.endswith(".csv"):
                csv_path = os.path.join(folder, file)

                try:
                    df = pd.read_csv(csv_path)

                    print(f"📄 File: {csv_path}")
                    print(f"   Rows: {len(df)}")
                    print(f"   Columns ({len(df.columns)}): {list(df.columns)}\n")

                except Exception as e:
                    print(f"❌ Error reading {csv_path}: {e}\n")


# Run the scanner
analyze_csv_files(ROOT_DIR)
