
import pandas as pd
from pathlib import Path

# Project paths
project_dir = Path(__file__).resolve().parent.parent
input_file = project_dir / "data" / "Sample_Superstore.xls"
output_file = project_dir / "data" / "superstore_cleaned.csv"

# Load dataset
df = pd.read_excel(input_file)

# Standardize column names
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(r"[^a-z0-9]+", "_", regex=True)
    .str.strip("_")
)

# Remove exact duplicate rows
df = df.drop_duplicates()

# Clean text columns
text_columns = df.select_dtypes(include=["str", "object"]).columns
for col in text_columns:
    df[col] = df[col].apply(
        lambda value: value.strip() if isinstance(value, str) else value
    )

# Convert date columns
for col in ["order_date", "ship_date"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# Validate important fields
df = df.dropna(subset=["order_id", "order_date", "sales", "profit"])

# Save cleaned dataset
df.to_csv(output_file, index=False)

print("Cleaning completed!")
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Missing values:", int(df.isnull().sum().sum()))
print("Duplicates:", int(df.duplicated().sum()))
print("Saved to:", output_file)
