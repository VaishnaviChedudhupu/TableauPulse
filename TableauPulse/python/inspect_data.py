import pandas as pd
from pathlib import Path

# Locate the dataset
project_dir = Path(__file__).resolve().parent.parent
file_path = project_dir / "data" / "Sample_Superstore.xls"

# Load the Excel file
df = pd.read_excel(file_path)

# Inspect the dataset
print("\n--- First 5 Rows ---")
print(df.head())

print("\n--- Dataset Shape ---")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

print("\n--- Column Names ---")
print(df.columns.tolist())

print("\n--- Data Types ---")
print(df.dtypes)

print("\n--- Missing Values ---")
print(df.isnull().sum())

print("\n--- Duplicate Rows ---")
print(df.duplicated().sum())

print("\n--- Summary Statistics ---")
print(df.describe(include="all").T)
