
import os
import re
import requests
import pandas as pd


DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "superstore_cleaned.csv",
)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"

REQUIRED_COLUMNS = ["sales", "profit", "category"]

# Keep the AI interpretation short enough to fit the dashboard.
AI_MAX_TOKENS = 350


def load_sales_data():
    """Load and validate the cleaned Superstore dataset."""
    df = pd.read_csv(DATA_PATH)
    df.columns = [
        re.sub(r"\s+", "_", str(column).strip().lower())
        for column in df.columns
    ]

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    source_records = len(df)

    for column in ["sales", "profit", "quantity", "discount"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["category"] = df["category"].astype("string").str.strip()

    df = df.dropna(subset=["sales", "profit", "category"])
    df = df[df["category"] != ""]

    df.attrs["source_records"] = source_records
    df.attrs["excluded_records"] = source_records - len(df)

    return df


def safe_margin(sales, profit):
    if pd.isna(sales) or sales == 0:
        return None
    return (profit / sales) * 100


def money(value):
    return f"${value:,.2f}"


def percent(value):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def get_value(row, column, default="Unknown"):
    if column not in row.index or pd.isna(row[column]):
        return default
    return str(row[column])


def aggregate_performance(df, group_column):
    """Aggregate sales and profit, then calculate margin."""
    result = (
        df.groupby(group_column, dropna=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            records=("profit", "size"),
        )
        .reset_index()
    )

    result["margin"] = result.apply(
        lambda row: safe_margin(row["sales"], row["profit"]),
        axis=1,
    )

    return result


def make_finding(
    title,
    severity,
    evidence,
    interpretation,
    action,
    limitations,
):
    return {
        "title": title,
        "severity": severity,
        "evidence": evidence,
        "interpretation": interpretation,
        "action": action,
        "recommendation": action,
        "limitations": limitations,
    }


def analyze_categories(df):
    findings = []

    category_stats = aggregate_performance(df, "category")
    category_stats = category_stats.sort_values("margin")

    worst = category_stats.iloc[0]
    best = category_stats.iloc[-1]

    findings.append(
        make_finding(
            title=f"Lowest-margin category: {worst['category']}",
            severity="High" if worst["margin"] < 5 else "Medium",
            evidence=(
                f"Sales: {money(worst['sales'])}. "
                f"Profit: {money(worst['profit'])}. "
                f"Margin: {percent(worst['margin'])}. "
                f"Records: {int(worst['records']):,}."
            ),
            interpretation=(
                f"{worst['category']} has the lowest aggregate profit margin "
                "among the categories in this dataset."
            ),
            action=(
                "Review product-level profitability, shipping costs, pricing, "
                "and discount patterns in this category before making changes."
            ),
            limitations=(
                "The dataset does not establish which factor caused the margin "
                "result. Margin is calculated as aggregate profit divided by sales."
            ),
        )
    )

    findings.append(
        make_finding(
            title=f"Strongest-margin category: {best['category']}",
            severity="Positive",
            evidence=(
                f"Sales: {money(best['sales'])}. "
                f"Profit: {money(best['profit'])}. "
                f"Margin: {percent(best['margin'])}. "
                f"Records: {int(best['records']):,}."
            ),
            interpretation=(
                f"{best['category']} has the highest aggregate profit margin "
                "among the categories in this dataset."
            ),
            action=(
                "Review its product mix and sales patterns to identify practices "
                "worth investigating in other categories."
            ),
            limitations=(
                "The available data may not include all operating costs or "
                "explain why this category performs better."
            ),
        )
    )

    return findings


def analyze_subcategories(df):
    findings = []

    if "sub_category" not in df.columns:
        return findings

    stats = aggregate_performance(df, "sub_category")
    loss_makers = stats[stats["profit"] < 0].sort_values("profit")

    if not loss_makers.empty:
        worst = loss_makers.iloc[0]

        findings.append(
            make_finding(
                title=f"Loss-making subcategory: {worst['sub_category']}",
                severity="High",
                evidence=(
                    f"Sales: {money(worst['sales'])}. "
                    f"Profit: {money(worst['profit'])}. "
                    f"Margin: {percent(worst['margin'])}. "
                    f"Records: {int(worst['records']):,}. "
                    f"Loss-making subcategories: {len(loss_makers)}."
                ),
                interpretation=(
                    f"{worst['sub_category']} has the largest aggregate loss "
                    "among the subcategories."
                ),
                action=(
                    "Inspect the products and transactions contributing to this "
                    "loss before changing pricing or discount policies."
                ),
                limitations=(
                    "An aggregate loss does not mean every product or transaction "
                    "in the subcategory is unprofitable."
                ),
            )
        )

    if "region" in df.columns:
        regional = (
            df.groupby(["sub_category", "region"], dropna=False)
            .agg(
                sales=("sales", "sum"),
                profit=("profit", "sum"),
                records=("profit", "size"),
            )
            .reset_index()
        )

        regional["margin"] = regional.apply(
            lambda row: safe_margin(row["sales"], row["profit"]),
            axis=1,
        )

        regional_losses = regional[regional["profit"] < 0]

        if not regional_losses.empty:
            regional_losses = regional_losses.sort_values("profit")
            worst_region = regional_losses.iloc[0]

            subcategory = worst_region["sub_category"]
            region = worst_region["region"]

            evidence = (
                f"Subcategory: {subcategory}. Region: {region}. "
                f"Sales: {money(worst_region['sales'])}. "
                f"Profit: {money(worst_region['profit'])}. "
                f"Margin: {percent(worst_region['margin'])}. "
                f"Records: {int(worst_region['records']):,}. "
                f"Loss-making subcategory-region combinations: "
                f"{len(regional_losses)}."
            )

            findings.append(
                make_finding(
                    title=(
                        f"Regional loss to investigate: "
                        f"{subcategory} in {region}"
                    ),
                    severity="High",
                    evidence=evidence,
                    interpretation=(
                        "This subcategory-region combination has the largest "
                        "aggregate loss among the combinations in the dataset."
                    ),
                    action=(
                        "Investigate its products and discount distribution, then "
                        "compare the same subcategory in other regions."
                    ),
                    limitations=(
                        "Regional differences are observational and do not prove "
                        "that location caused the loss."
                    ),
                )
            )

            subset = df[
                (df["sub_category"] == subcategory)
                & (df["region"] == region)
            ].copy()

            product_key = (
                "product_id"
                if "product_id" in subset.columns
                else "product_name"
                if "product_name" in subset.columns
                else None
            )

            if product_key:
                product_stats = (
                    subset.groupby(product_key, dropna=False)
                    .agg(
                        sales=("sales", "sum"),
                        profit=("profit", "sum"),
                        records=("profit", "size"),
                    )
                    .reset_index()
                )

                product_stats["margin"] = product_stats.apply(
                    lambda row: safe_margin(
                        row["sales"],
                        row["profit"],
                    ),
                    axis=1,
                )

                product_stats = product_stats[
                    product_stats["profit"] < 0
                ].sort_values("profit")

                if not product_stats.empty:
                    top_products = product_stats.head(3)
                    product_lines = []

                    for _, product in top_products.iterrows():
                        product_id = get_value(product, product_key)

                        if (
                            product_key == "product_id"
                            and "product_name" in subset.columns
                        ):
                            names = subset.loc[
                                subset["product_id"] == product[product_key],
                                "product_name",
                            ].dropna()

                            product_name = (
                                str(names.iloc[0])
                                if not names.empty
                                else "Name unavailable"
                            )
                            product_label = (
                                f"{product_id} ({product_name})"
                            )
                        else:
                            product_label = product_id

                        product_lines.append(
                            f"{product_label}: "
                            f"profit {money(product['profit'])}, "
                            f"sales {money(product['sales'])}, "
                            f"margin {percent(product['margin'])}, "
                            f"{int(product['records'])} records"
                        )

                    findings.append(
                        make_finding(
                            title=(
                                f"Products contributing to "
                                f"{subcategory} losses in {region}"
                            ),
                            severity="High",
                            evidence=(
                                "Largest loss-making products in this subset: "
                                + "; ".join(product_lines)
                                + f". Number of loss-making products: "
                                f"{len(product_stats)}."
                            ),
                            interpretation=(
                                "These products have the largest aggregate losses "
                                "within the selected subcategory-region combination."
                            ),
                            action=(
                                "Review each listed product's transaction details, "
                                "discounts, sales volume, and fulfillment costs. "
                                "Prioritize products with repeated losses, not just "
                                "the largest single loss."
                            ),
                            limitations=(
                                "Small record counts can make product-level results "
                                "unstable. The dataset may not contain all costs."
                            ),
                        )
                    )

            if "discount" in subset.columns:
                discount_data = subset.dropna(
                    subset=["discount"]
                ).copy()

                if not discount_data.empty:
                    discount_data["discount_band"] = pd.cut(
                        discount_data["discount"],
                        bins=[-0.001, 0, 0.10, 0.20, 0.30, 0.50, 1.0],
                        labels=[
                            "No discount",
                            "Above 0–10%",
                            "Above 10–20%",
                            "Above 20–30%",
                            "Above 30–50%",
                            "Above 50–100%",
                        ],
                        include_lowest=True,
                    )

                    discount_stats = (
                        discount_data.groupby(
                            "discount_band",
                            observed=False,
                            dropna=False,
                        )
                        .agg(
                            sales=("sales", "sum"),
                            profit=("profit", "sum"),
                            records=("profit", "size"),
                        )
                        .reset_index()
                    )

                    discount_stats["margin"] = discount_stats.apply(
                        lambda row: safe_margin(
                            row["sales"],
                            row["profit"],
                        ),
                        axis=1,
                    )

                    discount_stats = discount_stats[
                        discount_stats["records"] > 0
                    ]

                    if not discount_stats.empty:
                        discount_lines = []

                        for _, band in discount_stats.iterrows():
                            discount_lines.append(
                                f"{band['discount_band']}: "
                                f"profit {money(band['profit'])}, "
                                f"sales {money(band['sales'])}, "
                                f"margin {percent(band['margin'])}, "
                                f"{int(band['records'])} records"
                            )

                        findings.append(
                            make_finding(
                                title=(
                                    f"Discount analysis: "
                                    f"{subcategory} in {region}"
                                ),
                                severity="Medium",
                                evidence="; ".join(discount_lines) + ".",
                                interpretation=(
                                    "Profitability differs across observed discount "
                                    "bands within this subset."
                                ),
                                action=(
                                    "Compare product mix and record counts across "
                                    "discount bands before deciding whether to change "
                                    "discount policies."
                                ),
                                limitations=(
                                    "Discount levels may be associated with losses "
                                    "without causing them. Product mix, order size, "
                                    "and other factors may differ across bands."
                                ),
                            )
                        )

            comparison = regional[
                (regional["sub_category"] == subcategory)
                & (regional["region"] != region)
            ].sort_values("margin", ascending=False)

            if not comparison.empty:
                comparison_lines = []

                for _, row in comparison.iterrows():
                    comparison_lines.append(
                        f"{row['region']}: "
                        f"profit {money(row['profit'])}, "
                        f"margin {percent(row['margin'])}, "
                        f"{int(row['records'])} records"
                    )

                findings.append(
                    make_finding(
                        title=f"Regional comparison: {subcategory}",
                        severity="Informational",
                        evidence=(
                            f"{region}: "
                            f"profit {money(worst_region['profit'])}, "
                            f"margin {percent(worst_region['margin'])}, "
                            f"{int(worst_region['records'])} records. "
                            f"Other regions: "
                            + "; ".join(comparison_lines)
                            + "."
                        ),
                        interpretation=(
                            "Comparing the same subcategory across regions can help "
                            "identify where further investigation may be useful."
                        ),
                        action=(
                            "Compare product mix, discount levels, and record counts "
                            "across regions before drawing conclusions."
                        ),
                        limitations=(
                            "Different sales volumes and product mixes can influence "
                            "regional results. This comparison does not establish cause."
                        ),
                    )
                )

    product_key = (
        "product_id"
        if "product_id" in df.columns
        else "product_name"
        if "product_name" in df.columns
        else None
    )

    if product_key:
        product_stats = (
            df.groupby(product_key, dropna=False)
            .agg(
                sales=("sales", "sum"),
                profit=("profit", "sum"),
                records=("profit", "size"),
            )
            .reset_index()
        )

        product_stats["margin"] = product_stats.apply(
            lambda row: safe_margin(row["sales"], row["profit"]),
            axis=1,
        )

        loss_products = product_stats[
            product_stats["profit"] < 0
        ].sort_values("profit")

        if not loss_products.empty:
            worst_product = loss_products.iloc[0]
            product_id = get_value(worst_product, product_key)

            product_name = product_id

            if (
                product_key == "product_id"
                and "product_name" in df.columns
            ):
                names = df.loc[
                    df["product_id"] == worst_product[product_key],
                    "product_name",
                ].dropna()

                if not names.empty:
                    product_name = f"{product_id} ({names.iloc[0]})"

            findings.append(
                make_finding(
                    title="Product with the largest aggregate loss",
                    severity="High",
                    evidence=(
                        f"Product: {product_name}. "
                        f"Sales: {money(worst_product['sales'])}. "
                        f"Profit: {money(worst_product['profit'])}. "
                        f"Margin: {percent(worst_product['margin'])}. "
                        f"Records: {int(worst_product['records']):,}. "
                        f"Products with negative aggregate profit: "
                        f"{len(loss_products)}."
                    ),
                    interpretation=(
                        "This product has the largest total loss when its records "
                        "are aggregated across the dataset."
                    ),
                    action=(
                        "Inspect the underlying transactions and validate costs, "
                        "discounts, and pricing before deciding whether the product "
                        "requires corrective action."
                    ),
                    limitations=(
                        "A product with few records may not represent a persistent "
                        "pattern. Aggregate profit does not identify the cause."
                    ),
                )
            )

    return findings


def analyze_discounts(df):
    findings = []

    if "discount" not in df.columns:
        return findings

    discount_data = df.dropna(subset=["discount"]).copy()

    discount_data["discount_band"] = pd.cut(
        discount_data["discount"],
        bins=[-0.001, 0, 0.10, 0.20, 0.30, 0.50, 1.0],
        labels=[
            "No discount",
            "Above 0–10%",
            "Above 10–20%",
            "Above 20–30%",
            "Above 30–50%",
            "Above 50–100%",
        ],
        include_lowest=True,
    )

    stats = (
        discount_data.groupby(
            "discount_band",
            observed=False,
            dropna=False,
        )
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            records=("profit", "size"),
        )
        .reset_index()
    )

    stats["margin"] = stats.apply(
        lambda row: safe_margin(row["sales"], row["profit"]),
        axis=1,
    )

    stats = stats[stats["records"] > 0]

    if stats.empty:
        return findings

    worst = stats.sort_values("margin").iloc[0]
    no_discount = stats[stats["discount_band"] == "No discount"]

    comparison = ""
    if not no_discount.empty:
        baseline = no_discount.iloc[0]
        difference = worst["margin"] - baseline["margin"]

        comparison = (
            f" No-discount margin: {percent(baseline['margin'])}. "
            f"Margin difference: {difference:.2f} percentage points."
        )

    band_evidence = "; ".join(
        f"{row['discount_band']}: "
        f"profit {money(row['profit'])}, "
        f"margin {percent(row['margin'])}, "
        f"{int(row['records'])} records"
        for _, row in stats.iterrows()
    )

    findings.append(
        make_finding(
            title=(
                f"Discount band with the lowest margin: "
                f"{worst['discount_band']}"
            ),
            severity="High" if worst["margin"] < 0 else "Medium",
            evidence=(
                f"Sales: {money(worst['sales'])}. "
                f"Profit: {money(worst['profit'])}. "
                f"Margin: {percent(worst['margin'])}. "
                f"Records: {int(worst['records']):,}."
                f"{comparison} All bands: {band_evidence}."
            ),
            interpretation=(
                "The lowest-margin discount band is an area worth investigating. "
                "Observed association does not prove discounting caused the loss."
            ),
            action=(
                "Compare products, regions, and transaction sizes across discount "
                "bands. Test any policy change against a clearly defined baseline."
            ),
            limitations=(
                "Discount bands can contain different product mixes and order sizes. "
                "This analysis is descriptive, not a causal experiment."
            ),
        )
    )

    return findings


def build_verified_summary(df, findings):
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    total_margin = safe_margin(total_sales, total_profit)

    lines = [
        "TABLEAUPULSE VERIFIED DATA SUMMARY",
        f"Valid records: {len(df):,}",
        f"Excluded records: {df.attrs.get('excluded_records', 0):,}",
        f"Total sales: {money(total_sales)}",
        f"Total profit: {money(total_profit)}",
        f"Overall profit margin: {percent(total_margin)}",
        "",
        "Key findings:",
    ]

    for index, finding in enumerate(findings, start=1):
        lines.append(f"{index}. {finding['title']}")
        lines.append(f"   Evidence: {finding['evidence']}")
        lines.append(f"   Interpretation: {finding['interpretation']}")
        lines.append(f"   Recommended action: {finding['recommendation']}")
        lines.append(f"   Limitations: {finding['limitations']}")

    return "\n".join(lines)


def explain_recommendations(findings):
    """Generate a concise AI interpretation from verified findings."""
    if not findings:
        return "No recommendations could be generated from the available data."

    # Give Ollama the key findings, not every detailed evidence paragraph.
    # Detailed evidence remains available in the Python-generated findings below.
    selected_titles = [
        "Lowest-margin category:",
        "Strongest-margin category:",
        "Loss-making subcategory:",
        "Regional loss to investigate:",
        "Discount band with the lowest margin:",
    ]

    selected_findings = []
    for prefix in selected_titles:
        for item in findings:
            if item["title"].startswith(prefix):
                selected_findings.append(item)
                break

    if not selected_findings:
        selected_findings = findings[:5]

    evidence_text = "\n".join(
        (
            f"- {item['title']}\n"
            f"  Evidence: {item['evidence']}\n"
            f"  Interpretation: {item['interpretation']}\n"
            f"  Suggested action: {item['recommendation']}\n"
            f"  Limitation: {item['limitations']}"
        )
        for item in selected_findings
    )

    prompt = f"""
You are a careful business data analyst writing a dashboard summary.

Use ONLY the verified findings supplied below. Do not invent numbers, facts,
causes, or external information. Do not claim that an association proves causation.

Write a concise answer in this exact structure:

### Overall interpretation
Write 2 to 3 short sentences summarizing the most important business patterns.
Mention the lowest-margin category and the most important loss or discount signal
when supported by the supplied findings.

### Recommended next steps
Give exactly 3 numbered actions. Make each action specific and practical.
Prioritize investigation before recommending business policy changes.

### Important caution
Write one short sentence explaining that these are descriptive findings and
do not prove causes.

Rules:
- Keep the entire response under 180 words.
- Do not repeat the full evidence or list all findings.
- Do not add a long introduction or conclusion.
- Do not use a "Next Steps" section in addition to the numbered actions.
- Do not end with an unfinished sentence.
- Use readable Markdown.

Verified findings:
{evidence_text}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": AI_MAX_TOKENS,
                    "temperature": 0.2,
                },
            },
            timeout=90,
        )
        response.raise_for_status()

        result = response.json().get("response", "").strip()

        if not result:
            return (
                "AI interpretation is empty. Please use the verified findings "
                "and recommended actions listed below."
            )

        # Remove common model-generated filler if present.
        result = re.sub(
            r"^\s*(Here is|Here's) (the |a )?(concise )?(business )?interpretation:?\s*",
            "",
            result,
            flags=re.IGNORECASE,
        )

        # Avoid displaying an answer that is clearly excessively long.
        words = result.split()
        if len(words) > 220:
            result = " ".join(words[:220]).rsplit(" ", 1)[0] + "…"

        return result

    except requests.RequestException:
        return (
            "AI interpretation is currently unavailable. The verified Python-"
            "generated findings and suggested actions are still available below."
        )
    except (ValueError, TypeError, KeyError):
        return (
            "AI interpretation could not be processed. The verified Python-"
            "generated findings and suggested actions are still available below."
        )


def get_business_recommendations():
    df = load_sales_data()

    findings = []
    findings.extend(analyze_categories(df))
    findings.extend(analyze_subcategories(df))
    findings.extend(analyze_discounts(df))

    summary = build_verified_summary(df, findings)
    ai_explanation = explain_recommendations(findings)

    return {
        "summary": summary,
        "ai_explanation": ai_explanation,
        "recommendations": findings,
        "data_quality": {
            "valid_records": len(df),
            "excluded_records": df.attrs.get("excluded_records", 0),
        },
    }


if __name__ == "__main__":
    result = get_business_recommendations()

    print(result["summary"])
    print("\nAI EXPLANATION\n")
    print(result["ai_explanation"])

    print("\nDETAILED RECOMMENDATIONS\n")
    for item in result["recommendations"]:
        print(f"\n{item['title']}")
        print(f"Severity: {item['severity']}")
        print(f"Evidence: {item['evidence']}")
        print(f"Interpretation: {item['interpretation']}")
        print(f"Recommended action: {item['recommendation']}")
        print(f"Limitations: {item['limitations']}")
