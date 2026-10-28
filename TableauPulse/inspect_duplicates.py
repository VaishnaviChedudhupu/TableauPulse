
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "data", "superstore_cleaned.csv"
)

df = pd.read_csv(DATA_PATH)

duplicates = df[
    df.duplicated(
        subset=["order_id", "product_id"],
        keep=False
    )
].sort_values(["order_id", "product_id"])

columns = [
    "row_id",
    "order_id",
    "order_date",
    "ship_date",
    "ship_mode",
    "customer_id",
    "product_id",
    "product_name",
    "sales",
    "quantity",
    "discount",
    "profit",
]

print("REPEATED ORDER-PRODUCT COMBINATIONS")
print("=" * 80)
print(duplicates[columns].to_string(index=False))
print("\nTotal rows to inspect:", len(duplicates))
