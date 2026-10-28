
import requests
from metrics import get_sales_metrics


def generate_insight(metrics):
    overall = next(
        row for row in metrics
        if row["category"] == "Overall"
    )

    categories = [
        row for row in metrics
        if row["category"] != "Overall"
    ]

    # Calculate comparisons using verified SQL metrics
    highest_margin = max(
        categories,
        key=lambda row: float(row["profit_margin_percent"])
    )

    lowest_margin = min(
        categories,
        key=lambda row: float(row["profit_margin_percent"])
    )

    highest_sales = max(
        categories,
        key=lambda row: float(row["total_sales"])
    )

    category_text = "\n".join(
        f"- {row['category']}: "
        f"Sales=${row['total_sales']:,.2f}, "
        f"Profit=${row['total_profit']:,.2f}, "
        f"Margin={row['profit_margin_percent']}%, "
        f"Orders={row['total_orders']}"
        for row in categories
    )

    # Calculate the key findings in Python, not with the LLM
    findings = (
        f"- Highest sales: {highest_sales['category']} "
        f"(${highest_sales['total_sales']:,.2f})\n"
        f"- Highest profit margin: {highest_margin['category']} "
        f"({highest_margin['profit_margin_percent']}%)\n"
        f"- Lowest profit margin: {lowest_margin['category']} "
        f"({lowest_margin['profit_margin_percent']}%)"
    )

    prompt = f"""
You are a retail business analyst.
Explain the verified findings in clear, professional language.

Overall metrics:
- Sales: ${overall['total_sales']:,.2f}
- Profit: ${overall['total_profit']:,.2f}
- Profit margin: {overall['profit_margin_percent']}%
- Orders: {overall['total_orders']}

Category metrics:
{category_text}

Pre-calculated findings:
{findings}

Write:
1. A short performance summary.
2. Two observations based on the findings.
3. One recommendation for further analysis.

Rules:
- Treat the pre-calculated findings as correct.
- Do not reverse or contradict any comparison.
- Do not invent causes or trends.
- Do not invent numbers.
- Recommend investigating the lowest-margin category without claiming
  to know the cause of its margin.
- Keep the answer concise.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False
        },
        timeout=180
    )

    response.raise_for_status()
    return response.json()["response"]


if __name__ == "__main__":
    metrics = get_sales_metrics()

    overall = next(
        row for row in metrics
        if row["category"] == "Overall"
    )

    print("\n--- VERIFIED OVERALL METRICS ---")
    print(f"Total Sales: ${overall['total_sales']:,.2f}")
    print(f"Total Profit: ${overall['total_profit']:,.2f}")
    print(f"Profit Margin: {overall['profit_margin_percent']}%")
    print(f"Total Orders: {overall['total_orders']}")

    print("\n--- CATEGORY COMPARISONS (PYTHON) ---")
    categories = [
        row for row in metrics
        if row["category"] != "Overall"
    ]

    for row in categories:
        print(
            f"{row['category']}: "
            f"Sales=${row['total_sales']:,.2f}, "
            f"Profit=${row['total_profit']:,.2f}, "
            f"Margin={row['profit_margin_percent']}%"
        )

    print("\n--- TABLEAUPULSE AI INSIGHTS ---")
    print(generate_insight(metrics))
