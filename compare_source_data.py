
import os
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_PATH = os.path.join(BASE_DIR, "data", "Sample_Superstore.xls")
CLEANED_PATH = os.path.join(BASE_DIR, "data", "superstore_cleaned.csv")


def normalize_columns(df):
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
        for c in df.columns
    ]
    return df


def main():
    source = normalize_columns(pd.read_excel(SOURCE_PATH))
    cleaned = normalize_columns(pd.read_csv(CLEANED_PATH))

    print("=" * 65)
    print("TABLEAUPULSE - SOURCE VS CLEANED DATA VALIDATION")
    print("=" * 65)

    if list(source.columns) != list(cleaned.columns):
        print("FAIL: Column names or order differ.")
        print("Source:", source.columns.tolist())
        print("Cleaned:", cleaned.columns.tolist())
        return

    print("Source rows:", len(source))
    print("Cleaned rows:", len(cleaned))

    if len(source) != len(cleaned):
        print("FAIL: Row counts differ.")
        return

    # Compare values while ignoring harmless type differences
    # introduced by reading Excel versus CSV.
    source = source.fillna("").astype(str).reset_index(drop=True)
    cleaned = cleaned.fillna("").astype(str).reset_index(drop=True)

    differences = source.ne(cleaned)
    mismatch_count = int(differences.sum().sum())

    print("\nTotal cell differences:", mismatch_count)

    if mismatch_count == 0:
        print("PASS: All cell values match.")
    else:
        print("FAIL: Some cell values differ.")
        rows, cols = differences.to_numpy().nonzero()

        for row, col in list(zip(rows, cols))[:20]:
            column = source.columns[col]
            print(
                f"Row {row + 1}, column '{column}': "
                f"source={source.iloc[row, col]!r}, "
                f"cleaned={cleaned.iloc[row, col]!r}"
            )

        if mismatch_count > 20:
            print("Only the first 20 differences are shown.")

    print("\nValidation complete. No files were modified.")


if __name__ == "__main__":
    main()
