
import requests
from metrics import get_sales_metrics


def answer_question(question, metrics):
    overall = next(
        row for row in metrics
        if row["category"] == "Overall"
    )

    categories = [
        row for row in metrics
        if row["category"] != "Overall"
    ]

    q = question.lower().strip().rstrip("?!. ")

    # Overall business questions
    if "total profit" in q:
        return (
            f"Total profit is ${overall['total_profit']:,.2f}.",
            "Verified MySQL metrics"
        )

    if "total sales" in q:
        return (
            f"Total sales are ${overall['total_sales']:,.2f}.",
            "Verified MySQL metrics"
        )

    if "total orders" in q or "number of orders" in q:
        return (
            f"Total distinct orders: {overall['total_orders']:,}.",
            "Verified MySQL metrics"
        )

    # Category comparisons
    if "lowest profit margin" in q or "worst margin" in q:
        row = min(
            categories,
            key=lambda x: float(x["profit_margin_percent"])
        )
        return (
            f"{row['category']} has the lowest profit margin "
            f"at {row['profit_margin_percent']}%.",
            "Verified MySQL category metrics"
        )

    if "highest profit margin" in q or "best margin" in q:
        row = max(
            categories,
            key=lambda x: float(x["profit_margin_percent"])
        )
        return (
            f"{row['category']} has the highest profit margin "
            f"at {row['profit_margin_percent']}%.",
            "Verified MySQL category metrics"
        )

    if "highest sales" in q or "most sales" in q:
        row = max(categories, key=lambda x: float(x["total_sales"]))
        return (
            f"{row['category']} has the highest sales "
            f"at ${row['total_sales']:,.2f}.",
            "Verified MySQL category metrics"
        )

    if "lowest sales" in q or "least sales" in q:
        row = min(categories, key=lambda x: float(x["total_sales"]))
        return (
            f"{row['category']} has the lowest sales "
            f"at ${row['total_sales']:,.2f}.",
            "Verified MySQL category metrics"
        )

    # Questions about a particular category
    for row in categories:
        category = row["category"].lower()

        if category in q:
            if "profit margin" in q or "margin" in q:
                return (
                    f"{row['category']} profit margin is "
                    f"{row['profit_margin_percent']}%.",
                    "Verified MySQL category metrics"
                )

            if "profit" in q:
                return (
                    f"{row['category']} total profit is "
                    f"${row['total_profit']:,.2f}.",
                    "Verified MySQL category metrics"
                )

            if "sales" in q or "revenue" in q:
                return (
                    f"{row['category']} total sales are "
                    f"${row['total_sales']:,.2f}.",
                    "Verified MySQL category metrics"
                )

            if "order" in q:
                return (
                    f"{row['category']} has "
                    f"{row['total_orders']:,} distinct orders.",
                    "Verified MySQL category metrics"
                )

    # Use the LLM for other questions
    category_summary = "\n".join(
        f"- {row['category']}: "
        f"Sales ${row['total_sales']:,.2f}, "
        f"Profit ${row['total_profit']:,.2f}, "
        f"Margin {row['profit_margin_percent']}%"
        for row in categories
    )

    evidence = (
        f"Total sales: ${overall['total_sales']:,.2f}\n"
        f"Total profit: ${overall['total_profit']:,.2f}\n"
        f"Profit margin: {overall['profit_margin_percent']}%\n"
        f"Total orders: {overall['total_orders']}\n\n"
        f"Category metrics:\n{category_summary}"
    )

    prompt = f"""
You are TableauPulse, a retail business analyst.

User question: {question}

Verified database evidence:
{evidence}

Answer briefly using only the evidence.
Do not invent numbers, causes, or trends.
If the evidence is insufficient, say so.
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0}
            },
            timeout=180
        )
        response.raise_for_status()

        return (
            response.json()["response"].strip(),
            "Ollama using verified SQL evidence"
        )

    except requests.RequestException:
        return (
            "The AI service is unavailable. Please try again.",
            "Ollama connection error"
        )


if __name__ == "__main__":
    metrics = get_sales_metrics()

    print("TableauPulse — Ask a question about Superstore")
    question = input("\nYour question: ").strip()

    if not question:
        print("Please enter a question.")
    else:
        answer, source = answer_question(question, metrics)

        print("\n--- ANSWER ---")
        print(answer)

        print("\n--- SOURCE ---")
        print(source)
