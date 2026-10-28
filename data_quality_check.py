
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "data", "superstore_cleaned.csv"
)


def main():
    print("=" * 65)
    print("TABLEAUPULSE - DATA QUALITY AUDIT")
    print("=" * 65)

    if not os.path.exists(DATA_PATH):
        print(f"ERROR: Dataset not found at:\n{DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)

    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    print(f"\nDataset: {DATA_PATH}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    print("\n1. COLUMN DATA TYPES")
    print("-" * 65)
    print(df.dtypes.to_string())

    print("\n2. MISSING VALUES")
    print("-" * 65)

    missing = df.isna().sum()
    missing_report = pd.DataFrame({
        "missing_count": missing,
        "missing_percent": (
            missing / len(df) * 100 if len(df) else 0
        ),
    })

    missing_report = missing_report.sort_values(
        "missing_count", ascending=False
    )

    print(missing_report.to_string())

    print("\n3. EXACT DUPLICATE ROWS")
    print("-" * 65)

    exact_duplicates = int(df.duplicated().sum())
    print(f"Exact duplicate rows: {exact_duplicates:,}")

    print("\n4. POTENTIAL ORDER-LINE DUPLICATES")
    print("-" * 65)

    line_keys = [
        "order_id",
        "product_id",
    ]

    if all(column in df.columns for column in line_keys):
        repeated_keys = int(
            df.duplicated(subset=line_keys, keep=False).sum()
        )

        print(
            "Rows sharing the same order_id and product_id: "
            f"{repeated_keys:,}"
        )
        print(
            "These are potential duplicates only. "
            "Check the source before removing any."
        )
    else:
        print(
            "Skipped: order_id or product_id is unavailable."
        )

    print("\n5. NUMERIC VALUE CHECKS")
    print("-" * 65)

    numeric_columns = [
        "sales",
        "profit",
        "quantity",
        "discount",
    ]

    for column in numeric_columns:
        if column not in df.columns:
            print(f"{column}: column not found")
            continue

        original = df[column]
        converted = pd.to_numeric(original, errors="coerce")

        invalid = int(
            (original.notna() & converted.isna()).sum()
        )

        print(f"\n{column}")
        print(f"  Invalid numeric values: {invalid:,}")

        if converted.notna().any():
            print(f"  Minimum: {converted.min()}")
            print(f"  Maximum: {converted.max()}")
            print(f"  Negative values: {(converted < 0).sum():,}")

            if column == "discount":
                outside_range = (
                    (converted < 0) | (converted > 1)
                )
                print(
                    "  Values outside the expected 0–1 range: "
                    f"{outside_range.sum():,}"
                )

            if column == "quantity":
                non_integer = (
                    converted.notna()
                    & (converted % 1 != 0)
                )
                print(
                    f"  Non-integer quantities: "
                    f"{non_integer.sum():,}"
                )

    print("\n6. DATE VALIDATION")
    print("-" * 65)

    for column in ["order_date", "ship_date"]:
        if column not in df.columns:
            print(f"{column}: column not found")
            continue

        parsed = pd.to_datetime(
            df[column], errors="coerce"
        )

        invalid_dates = int(
            (df[column].notna() & parsed.isna()).sum()
        )

        print(f"\n{column}")
        print(f"  Invalid dates: {invalid_dates:,}")

        if parsed.notna().any():
            print(f"  Earliest: {parsed.min()}")
            print(f"  Latest: {parsed.max()}")

    if {"order_date", "ship_date"}.issubset(df.columns):
        order_dates = pd.to_datetime(
            df["order_date"], errors="coerce"
        )
        ship_dates = pd.to_datetime(
            df["ship_date"], errors="coerce"
        )

        reversed_dates = (
            order_dates.notna()
            & ship_dates.notna()
            & (ship_dates < order_dates)
        )

        print(
            "\nRows where shipping precedes ordering: "
            f"{reversed_dates.sum():,}"
        )

    print("\n7. PROFITABILITY RECONCILIATION")
    print("-" * 65)

    if {"sales", "profit"}.issubset(df.columns):
        sales = pd.to_numeric(
            df["sales"], errors="coerce"
        )
        profit = pd.to_numeric(
            df["profit"], errors="coerce"
        )

        valid = sales.notna() & profit.notna()

        total_sales = sales[valid].sum()
        total_profit = profit[valid].sum()

        margin = (
            total_profit / total_sales * 100
            if total_sales != 0
            else None
        )

        print(f"Rows with numeric sales and profit: {valid.sum():,}")
        print(f"Total sales: ${total_sales:,.2f}")
        print(f"Total profit: ${total_profit:,.2f}")
        print(
            "Profit margin: "
            f"{margin:.2f}%"
            if margin is not None
            else "Profit margin: N/A"
        )

    print("\n" + "=" * 65)
    print("AUDIT COMPLETE - REVIEW FLAGS BEFORE CHANGING DATA")
    print("=" * 65)


if __name__ == "__main__":
    main()
