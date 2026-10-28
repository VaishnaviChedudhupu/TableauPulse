
import os
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "data", "Sample_Superstore.xls"
)


def normalize_columns(df):
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
        for c in df.columns
    ]
    return df


def main():
    df = normalize_columns(pd.read_excel(DATA_PATH))

    print("=" * 65)
    print("TABLEAUPULSE - PRODUCT CONSISTENCY AUDIT")
    print("=" * 65)

    required = [
        "product_id", "product_name",
        "category", "sub_category"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        print("Missing required columns:", missing)
        print("Available columns:", df.columns.tolist())
        return

    print("\n1. PRODUCT ID MAPPING")
    print("-" * 65)

    names_per_id = df.groupby("product_id")["product_name"].nunique()
    inconsistent_names = names_per_id[names_per_id > 1]

    print("Unique product IDs:", df["product_id"].nunique())
    print("IDs mapped to multiple product names:", len(inconsistent_names))

    if not inconsistent_names.empty:
        print(
            df[df["product_id"].isin(inconsistent_names.index)]
            [["product_id", "product_name"]]
            .drop_duplicates()
            .sort_values("product_id")
            .to_string(index=False)
        )

    print("\n2. CATEGORY CONSISTENCY")
    print("-" * 65)

    categories_per_id = df.groupby("product_id")["category"].nunique()
    inconsistent_categories = categories_per_id[categories_per_id > 1]

    print("IDs mapped to multiple categories:", len(inconsistent_categories))

    if not inconsistent_categories.empty:
        print(
            df[df["product_id"].isin(inconsistent_categories.index)]
            [["product_id", "product_name", "category"]]
            .drop_duplicates()
            .sort_values("product_id")
            .to_string(index=False)
        )

    print("\n3. SUBCATEGORY CONSISTENCY")
    print("-" * 65)

    subcategories_per_id = (
        df.groupby("product_id")["sub_category"].nunique()
    )
    inconsistent_subcategories = subcategories_per_id[
        subcategories_per_id > 1
    ]

    print(
        "IDs mapped to multiple subcategories:",
        len(inconsistent_subcategories)
    )

    if not inconsistent_subcategories.empty:
        print(
            df[df["product_id"].isin(inconsistent_subcategories.index)]
            [["product_id", "product_name", "category", "sub_category"]]
            .drop_duplicates()
            .sort_values("product_id")
            .to_string(index=False)
        )

    print("\nAudit complete. Original data was not modified.")


if __name__ == "__main__":
    main()
