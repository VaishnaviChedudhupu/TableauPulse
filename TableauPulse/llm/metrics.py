
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# Load environment variables from the project root
project_dir = Path(__file__).resolve().parent.parent
load_dotenv(project_dir / ".env")


def get_sales_metrics():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=3306,
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "tableaupulse")
    )

    try:
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                'Overall' AS category,
                ROUND(SUM(sales), 2) AS total_sales,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND(
                    SUM(profit) / NULLIF(SUM(sales), 0) * 100,
                    2
                ) AS profit_margin_percent,
                COUNT(DISTINCT order_id) AS total_orders
            FROM superstore

            UNION ALL

            SELECT
                category,
                ROUND(SUM(sales), 2) AS total_sales,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND(
                    SUM(profit) / NULLIF(SUM(sales), 0) * 100,
                    2
                ) AS profit_margin_percent,
                COUNT(DISTINCT order_id) AS total_orders
            FROM superstore
            GROUP BY category
        """

        cursor.execute(query)
        metrics = cursor.fetchall()

        return metrics

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    results = get_sales_metrics()

    print("\n--- VERIFIED SALES METRICS ---")

    for row in results:
        print(f"\nCategory: {row['category']}")
        print(f"Total Sales: ${row['total_sales']:,.2f}")
        print(f"Total Profit: ${row['total_profit']:,.2f}")
        print(f"Profit Margin: {row['profit_margin_percent']}%")
        print(f"Total Orders: {row['total_orders']}")
