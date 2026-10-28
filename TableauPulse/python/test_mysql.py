
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# Load environment variables from the project root
project_dir = Path(__file__).resolve().parent.parent
load_dotenv(project_dir / ".env")

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=3306,
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "tableaupulse")
    )

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM superstore")
    total_rows = cursor.fetchone()[0]

    print("MySQL connection successful!")
    print(f"Rows in superstore: {total_rows}")

    cursor.close()
    conn.close()

except mysql.connector.Error as error:
    print("MySQL connection failed:", error)
