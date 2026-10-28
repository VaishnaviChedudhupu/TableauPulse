
import os
import pandas as pd
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv

# Locate the project directory and load environment variables
project_dir = Path(__file__).resolve().parent.parent
load_dotenv(project_dir / ".env")

# Locate the cleaned CSV file
csv_file = project_dir / "data" / "superstore_cleaned.csv"

# Read cleaned data
df = pd.read_csv(csv_file)

# Connect to MySQL
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=3306,
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "tableaupulse")
)

cursor = conn.cursor()

try:
    # Create table using the CSV columns
    columns = ", ".join(f"`{col}` TEXT" for col in df.columns)
    cursor.execute(f"CREATE TABLE IF NOT EXISTS superstore ({columns})")

    # Insert rows
    placeholders = ", ".join(["%s"] * len(df.columns))
    column_names = ", ".join(f"`{col}`" for col in df.columns)
    query = f"INSERT INTO superstore ({column_names}) VALUES ({placeholders})"

    data = [
        tuple(None if pd.isna(value) else str(value) for value in row)
        for row in df.itertuples(index=False, name=None)
    ]

    cursor.executemany(query, data)
    conn.commit()

    print(f"Successfully loaded {cursor.rowcount} rows into MySQL.")

finally:
    cursor.close()
    conn.close()
