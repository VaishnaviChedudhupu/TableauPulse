
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "data", "Sample_Superstore.xls"
)


def main():
    df = pd.read_excel(DATA_PATH)

    df.columns = [
        str(c).strip().lower().replace("/", "_").replace(" ", "_")
        for c in df.columns
    ]

    print("=" * 65)
    print("TABLEAUPULSE - FINANCIAL DATA VALIDATION")
    print("=" * 65)

    print("\n1. FINANCIAL TOTALS")
    print("-" * 65)

    for column in ["sales", "profit", "discount"]:
        if column in df.columns:
            print(f"{column.title()} total: {df[column].sum():,.2f}")

    if {"sales", "profit"}.issubset(df.columns):
        total_sales = df["sales"].sum()
        total_profit = df["profit"].sum()

        margin = (
            total_profit / total_sales * 100
            if total_sales else 0
        )

        print(f"Overall profit margin: {margin:.2f}%")

    print("\n2. SALES AND PROFIT BY CATEGORY")
    print("-" * 65)

    if {"category", "sales", "profit"}.issubset(df.columns):
        category_summary = (
            df.groupby("category")
            .agg(
                records=("sales", "size"),
                sales=("sales", "sum"),
                profit=("profit", "sum"),
            )
            .reset_index()
        )

        category_summary["profit_margin_pct"] = (
            category_summary["profit"]
            / category_summary["sales"] * 100
        )

        print(category_summary.round(2).to_string(index=False))

    print("\n3. CHECK FOR UNUSUAL FINANCIAL VALUES")
    print("-" * 65)

    for column in ["sales", "profit", "discount"]:
        if column in df.columns:
            print(f"\n{column.title()}:")
            print(f"  Missing: {df[column].isna().sum():,}")
            print(f"  Negative: {(df[column] < 0).sum():,}")

    print("\n4. SAMPLE RECORDS")
    print("-" * 65)

    sample_columns = [
        c for c in [
            "row_id", "order_id", "product_id",
            "sales", "quantity", "discount", "profit"
        ] if c in df.columns
    ]

    print(df[sample_columns].head(10).to_string(index=False))

    print("\nValidation report complete.")
    print("No data was modified.")


if __name__ == "__main__":
    main()
