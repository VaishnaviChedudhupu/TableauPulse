
import sys
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# 1. PROJECT PATHS AND IMPORTS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
LLM_DIR = PROJECT_DIR / "llm"

if str(LLM_DIR) not in sys.path:
    sys.path.insert(0, str(LLM_DIR))

from metrics import get_sales_metrics
from ask_question import answer_question
from recommendations import get_business_recommendations


# --------------------------------------------------
# 2. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="TableauPulse | Retail Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --------------------------------------------------
# 3. DARK THEME
# --------------------------------------------------

C = {
    "bg": "#0B1220",
    "surface": "#121D30",
    "surface2": "#19263B",
    "text": "#EDF2FC",
    "muted": "#9AAAC1",
    "border": "#283850",
    "accent": "#8BAAFF",
    "accent2": "#53D6B0",
    "negative": "#FF929C",
    "grid": "#283850",
}


# --------------------------------------------------
# 4. CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {C["bg"]};
        color: {C["text"]};
    }}

    [data-testid="stHeader"] {{
        background-color: {C["bg"]};
    }}

    [data-testid="stSidebar"] {{
        background-color: {C["surface"]};
    }}

    h1, h2, h3, h4, p, label {{
        color: {C["text"]};
    }}

    .tp-subtitle {{
        color: {C["muted"]};
        font-size: 15px;
    }}

    .tp-card {{
        background-color: {C["surface"]};
        border: 1px solid {C["border"]};
        border-radius: 14px;
        padding: 20px;
        min-height: 120px;
        overflow-wrap: anywhere;
    }}

    .tp-label {{
        color: {C["muted"]};
        font-size: 13px;
        margin-bottom: 10px;
    }}

    .tp-value {{
        color: {C["text"]};
        font-size: 27px;
        font-weight: 700;
    }}

    .tp-caption {{
        color: {C["muted"]};
        font-size: 12px;
        margin-top: 8px;
    }}

    [data-testid="stTabs"] button {{
        font-weight: 600;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {C["border"]};
        border-radius: 10px;
    }}

    div.stButton > button,
    div.stFormSubmitButton > button {{
        border-radius: 9px;
        font-weight: 600;
    }}

    hr {{
        border-color: {C["border"]};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

CHART_TEMPLATE = "plotly_dark"


# --------------------------------------------------
# 5. DATA LOADING AND HELPER FUNCTIONS
# --------------------------------------------------

@st.cache_data(ttl=60)
def load_metrics():
    return get_sales_metrics()


@st.cache_data(ttl=300)
def load_superstore_csv():
    possible_paths = [
        PROJECT_DIR / "data" / "superstore_cleaned.csv",
        PROJECT_DIR / "superstore_cleaned.csv",
    ]

    for path in possible_paths:
        if path.exists():
            df = pd.read_csv(path)
            df.columns = [
                str(col).strip().lower().replace(" ", "_")
                for col in df.columns
            ]
            return df

    return pd.DataFrame()


def find_column(df, *names):
    for name in names:
        if name in df.columns:
            return name
    return None


def money(value):
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def number(value):
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "N/A"


def percent(value):
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def style_chart(fig):
    fig.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor=C["surface"],
        plot_bgcolor=C["surface"],
        font=dict(color=C["text"]),
        margin=dict(l=15, r=15, t=55, b=15),
        title_font_size=17,
        legend_title_text="",
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor=C["border"],
    )

    fig.update_yaxes(
        gridcolor=C["grid"],
        zerolinecolor=C["border"],
    )

    return fig


# --------------------------------------------------
# 6. LOAD DATA
# --------------------------------------------------

try:
    metrics = load_metrics()
    sales_df = load_superstore_csv()

except Exception as error:
    st.error("Unable to load dashboard data.")
    st.code(str(error))
    st.info(
        "Check your MySQL connection in llm/metrics.py "
        "and make sure MySQL is running."
    )
    st.stop()


if not metrics:
    st.error("No metrics were returned from MySQL.")
    st.stop()


overall_rows = [
    row for row in metrics
    if str(row.get("category", "")).strip().lower() == "overall"
]

if not overall_rows:
    st.error(
        "Your SQL metrics must contain an Overall row "
        "and category rows."
    )
    st.stop()

overall = overall_rows[0]

categories = [
    row for row in metrics
    if str(row.get("category", "")).strip().lower() != "overall"
]

category_df = pd.DataFrame(categories)


# --------------------------------------------------
# 7. DASHBOARD HEADER
# --------------------------------------------------

st.markdown(
    f"""
    <h1 style="margin-bottom:0;">📊 TableauPulse</h1>
    <p class="tp-subtitle">
        Retail Intelligence · Sales Analytics · AI-powered Insights
    </p>
    """,
    unsafe_allow_html=True,
)

st.divider()


# --------------------------------------------------
# 8. KPI CARDS
# --------------------------------------------------

total_sales = overall.get("total_sales", 0)
total_profit = overall.get("total_profit", 0)
profit_margin = overall.get("profit_margin_percent", 0)
total_orders = overall.get("total_orders", 0)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpis = [
    (kpi1, "TOTAL SALES", money(total_sales), "Overall sales revenue"),
    (kpi2, "TOTAL PROFIT", money(total_profit), "Overall profit"),
    (kpi3, "PROFIT MARGIN", percent(profit_margin), "Profit as % of sales"),
    (kpi4, "TOTAL ORDERS", number(total_orders), "Order count from SQL"),
]

for col, label, value, caption in kpis:
    with col:
        st.markdown(
            f"""
            <div class="tp-card">
                <div class="tp-label">{label}</div>
                <div class="tp-value">{value}</div>
                <div class="tp-caption">{caption}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")


# --------------------------------------------------
# 9. SIX DASHBOARD TABS
# --------------------------------------------------

(
    tab_overview,
    tab_category,
    tab_region,
    tab_ai,
    tab_recommendations,
    tab_quality,
) = st.tabs(
    [
        "📈 Sales Overview",
        "📦 Category Analysis",
        "🌍 Regional Analysis",
        "🤖 AI Insights",
        "💡 Business Recommendations",
        "🔍 Data Quality",
    ]
)


# --------------------------------------------------
# TAB 1 — SALES OVERVIEW
# --------------------------------------------------

with tab_overview:
    st.subheader("Sales Performance Overview")
    st.caption("High-level business performance and sales trends.")

    if not category_df.empty and {
        "category", "total_sales"
    }.issubset(category_df.columns):

        chart1, chart2 = st.columns(2)

        with chart1:
            fig = px.bar(
                category_df,
                x="category",
                y="total_sales",
                title="Sales by Category",
                labels={
                    "category": "Category",
                    "total_sales": "Sales ($)",
                },
                text_auto=".2s",
                color="category",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width="stretch")

        with chart2:
            if "total_profit" in category_df.columns:
                fig = px.bar(
                    category_df,
                    x="category",
                    y="total_profit",
                    title="Profit by Category",
                    labels={
                        "category": "Category",
                        "total_profit": "Profit ($)",
                    },
                    text_auto=".2s",
                    color="category",
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, width="stretch")

    date_col = find_column(
        sales_df, "order_date", "orderdate", "date"
    )
    sales_col = find_column(sales_df, "sales", "revenue")

    if date_col and sales_col:
        trend_df = sales_df[[date_col, sales_col]].copy()

        trend_df[date_col] = pd.to_datetime(
            trend_df[date_col], errors="coerce"
        )
        trend_df[sales_col] = pd.to_numeric(
            trend_df[sales_col], errors="coerce"
        )
        trend_df = trend_df.dropna()

        if not trend_df.empty:
            trend_df["Month"] = (
                trend_df[date_col]
                .dt.to_period("M")
                .dt.to_timestamp()
            )

            monthly = (
                trend_df.groupby("Month", as_index=False)[sales_col]
                .sum()
                .sort_values("Month")
            )

            fig = px.line(
                monthly,
                x="Month",
                y=sales_col,
                title="Monthly Sales Trend",
                markers=True,
                labels={
                    "Month": "Month",
                    sales_col: "Sales ($)",
                },
            )

            fig.update_traces(line=dict(width=3))
            st.plotly_chart(fig, width="stretch")
    else:
        st.info(
            "Monthly sales trends require order_date and sales "
            "columns in your cleaned CSV."
        )

    with st.expander("View category KPI data"):
        if not category_df.empty:
            st.dataframe(
                category_df,
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No category data is available.")


# --------------------------------------------------
# TAB 2 — CATEGORY ANALYSIS
# --------------------------------------------------

with tab_category:
    st.subheader("Category Performance")
    st.caption("Compare category sales, profit and profitability.")

    if category_df.empty:
        st.warning("No category metrics are available.")
    else:
        if {
            "category", "profit_margin_percent"
        }.issubset(category_df.columns):

            fig = px.bar(
                category_df,
                x="category",
                y="profit_margin_percent",
                title="Profit Margin by Category",
                labels={
                    "category": "Category",
                    "profit_margin_percent": "Profit Margin (%)",
                },
                text_auto=".2f",
                color="category",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width="stretch")

        if {
            "total_sales", "total_profit", "category"
        }.issubset(category_df.columns):

            fig = px.scatter(
                category_df,
                x="total_sales",
                y="total_profit",
                size="total_sales",
                color="category",
                hover_name="category",
                title="Sales vs Profit by Category",
                labels={
                    "total_sales": "Sales ($)",
                    "total_profit": "Profit ($)",
                },
            )
            st.plotly_chart(fig, width="stretch")

        display_df = category_df.copy()

        if "total_sales" in display_df.columns:
            display_df["total_sales"] = display_df[
                "total_sales"
            ].apply(money)

        if "total_profit" in display_df.columns:
            display_df["total_profit"] = display_df[
                "total_profit"
            ].apply(money)

        if "profit_margin_percent" in display_df.columns:
            display_df["profit_margin_percent"] = display_df[
                "profit_margin_percent"
            ].apply(percent)

        if "total_orders" in display_df.columns:
            display_df["total_orders"] = display_df[
                "total_orders"
            ].apply(number)

        st.markdown("#### Category KPI Table")
        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True,
        )

    subcat_col = find_column(
        sales_df, "sub_category", "subcategory"
    )
    sales_col = find_column(sales_df, "sales", "revenue")
    profit_col = find_column(sales_df, "profit")

    if subcat_col and sales_col and profit_col:
        product_df = sales_df.copy()

        product_df[sales_col] = pd.to_numeric(
            product_df[sales_col], errors="coerce"
        )
        product_df[profit_col] = pd.to_numeric(
            product_df[profit_col], errors="coerce"
        )

        subcategory_summary = (
            product_df.groupby(subcat_col, as_index=False)
            .agg(
                Sales=(sales_col, "sum"),
                Profit=(profit_col, "sum"),
            )
            .sort_values("Profit")
        )

        st.markdown("#### Subcategory Profitability")

        fig = px.bar(
            subcategory_summary.head(10),
            x="Profit",
            y=subcat_col,
            orientation="h",
            title="10 Lowest-Profit Subcategories",
            labels={
                "Profit": "Profit ($)",
                subcat_col: "Subcategory",
            },
            color="Profit",
            color_continuous_scale="RdYlGn",
        )

        st.plotly_chart(fig, width="stretch")


# --------------------------------------------------
# TAB 3 — REGIONAL ANALYSIS
# --------------------------------------------------

with tab_region:
    st.subheader("Regional and Customer Analysis")
    st.caption(
        "Explore performance by region, segment and shipping method."
    )

    region_col = find_column(sales_df, "region")
    segment_col = find_column(sales_df, "segment")
    ship_col = find_column(sales_df, "ship_mode", "shipmode")
    sales_col = find_column(sales_df, "sales", "revenue")
    profit_col = find_column(sales_df, "profit")
    customer_col = find_column(
        sales_df, "customer_name", "customername"
    )

    if sales_df.empty:
        st.warning(
            "The cleaned CSV was not found. Check your data folder."
        )
    else:
        if region_col and sales_col and profit_col:
            regional_df = sales_df.copy()

            regional_df[sales_col] = pd.to_numeric(
                regional_df[sales_col], errors="coerce"
            )
            regional_df[profit_col] = pd.to_numeric(
                regional_df[profit_col], errors="coerce"
            )

            regional_summary = (
                regional_df.groupby(region_col, as_index=False)
                .agg(
                    Sales=(sales_col, "sum"),
                    Profit=(profit_col, "sum"),
                )
                .sort_values("Sales", ascending=False)
            )

            fig = px.bar(
                regional_summary,
                x=region_col,
                y=["Sales", "Profit"],
                barmode="group",
                title="Sales and Profit by Region",
                labels={
                    region_col: "Region",
                    "value": "Amount ($)",
                    "variable": "Metric",
                },
            )

            st.plotly_chart(fig, width="stretch")
        else:
            st.info(
                "Regional charts require region, sales and profit columns."
            )

        if segment_col and sales_col:
            segment_summary = (
                sales_df.assign(
                    _sales=pd.to_numeric(
                        sales_df[sales_col], errors="coerce"
                    )
                )
                .groupby(segment_col, as_index=False)
                .agg(Sales=("_sales", "sum"))
                .sort_values("Sales", ascending=False)
            )

            fig = px.pie(
                segment_summary,
                names=segment_col,
                values="Sales",
                title="Sales by Customer Segment",
                hole=0.45,
            )

            st.plotly_chart(fig, width="stretch")

        if ship_col and sales_col and profit_col:
            shipping_df = sales_df.copy()

            shipping_df[sales_col] = pd.to_numeric(
                shipping_df[sales_col], errors="coerce"
            )
            shipping_df[profit_col] = pd.to_numeric(
                shipping_df[profit_col], errors="coerce"
            )

            shipping_summary = (
                shipping_df.groupby(ship_col, as_index=False)
                .agg(
                    Sales=(sales_col, "sum"),
                    Profit=(profit_col, "sum"),
                )
            )

            fig = px.bar(
                shipping_summary,
                x=ship_col,
                y="Profit",
                title="Profit by Shipping Mode",
                labels={
                    ship_col: "Shipping Mode",
                    "Profit": "Profit ($)",
                },
                color="Profit",
            )

            st.plotly_chart(fig, width="stretch")

        if customer_col and sales_col:
            customer_summary = (
                sales_df.assign(
                    _sales=pd.to_numeric(
                        sales_df[sales_col], errors="coerce"
                    )
                )
                .groupby(customer_col, as_index=False)
                .agg(Sales=("_sales", "sum"))
                .sort_values("Sales", ascending=False)
                .head(10)
            )

            fig = px.bar(
                customer_summary,
                x="Sales",
                y=customer_col,
                orientation="h",
                title="Top 10 Customers by Sales",
                labels={
                    "Sales": "Sales ($)",
                    customer_col: "Customer",
                },
            )

            fig.update_layout(
                yaxis={"categoryorder": "total ascending"}
            )

            st.plotly_chart(fig, width="stretch")


# --------------------------------------------------
# TAB 4 — AI INSIGHTS
# --------------------------------------------------

with tab_ai:
    st.subheader("Ask TableauPulse")
    st.caption(
        "Ask questions about sales, profit, categories and performance."
    )

    st.markdown(
        f"""
        <div class="tp-card">
            <strong>🤖 Your AI Business Assistant</strong>
            <p class="tp-subtitle">
                Get answers using your sales metrics and local Ollama model.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    example_questions = [
        "What are the total sales?",
        "Which category has the lowest profit margin?",
        "Which category has the highest sales?",
        "What is the total profit?",
    ]

    selected_question = st.selectbox(
        "Try a sample question",
        ["Choose a sample question..."] + example_questions,
    )

    with st.form("ask_tableaupulse_form"):
        question = st.text_input(
            "Your question",
            value=(
                selected_question
                if selected_question != "Choose a sample question..."
                else ""
            ),
            placeholder="e.g. Which category performs best?",
        )

        submitted = st.form_submit_button(
            "✨ Generate Insight",
            width="stretch",
        )

    if submitted:
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Analyzing your sales data..."):
                try:
                    result = answer_question(question, metrics)

                    if isinstance(result, tuple):
                        answer = result[0]
                        source = (
                            result[1]
                            if len(result) > 1
                            else "Sales metrics"
                        )
                    else:
                        answer = result
                        source = "TableauPulse"

                    st.markdown("### 💡 Answer")
                    st.markdown(answer)
                    st.caption(f"Source: {source}")

                except Exception as error:
                    st.error("Unable to generate an answer.")
                    st.code(str(error))

    with st.expander("How does TableauPulse generate insights?"):
        st.write(
            "1. SQL and MySQL provide sales metrics. "
            "2. Python handles supported metric-based questions. "
            "3. Ollama generates natural-language explanations. "
            "Verify important business decisions against the underlying data."
        )


# --------------------------------------------------
# TAB 5 — BUSINESS RECOMMENDATIONS
# --------------------------------------------------

with tab_recommendations:
    st.subheader("💡 Business Recommendations")
    st.caption(
        "Explore calculated sales evidence, AI interpretation, "
        "and suggested actions."
    )

    if st.button(
        "🔄 Generate Business Recommendations",
        key="generate_recommendations",
    ):
        with st.spinner("Analyzing business performance..."):
            try:
                result = get_business_recommendations()
                st.session_state["business_recommendations"] = result
                st.session_state.pop("recommendations_error", None)

            except Exception as error:
                st.session_state.pop("business_recommendations", None)
                st.session_state["recommendations_error"] = str(error)

    if "recommendations_error" in st.session_state:
        st.error("Unable to generate recommendations.")
        st.code(st.session_state["recommendations_error"])

    result = st.session_state.get("business_recommendations")

    if result:
        recommendations = result.get("recommendations", [])
        data_quality = result.get("data_quality", {})

        # BUSINESS SNAPSHOT
        st.markdown("### 📌 Business Snapshot")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Valid Records",
            number(data_quality.get("valid_records", 0)),
        )
        col2.metric(
            "Excluded Records",
            number(data_quality.get("excluded_records", 0)),
        )
        col3.metric(
            "Findings Generated",
            number(len(recommendations)),
        )

        st.divider()

        # AI BUSINESS INTERPRETATION
        st.markdown("### 🤖 AI Business Interpretation")
        st.caption(
            "A concise interpretation of the calculated findings. "
            "Verify important decisions against the supporting evidence."
        )

        ai_explanation = str(
            result.get("ai_explanation", "")
        ).strip()

        if ai_explanation:
            # Normalize line breaks.
            clean_explanation = ai_explanation.replace("\r\n", "\n")
            clean_explanation = clean_explanation.replace("\r", "\n")

            # Remove Markdown heading markers.
            clean_explanation = re.sub(
                r"(?m)^\s{0,3}#{1,6}\s+",
                "",
                clean_explanation,
            )

            # Remove common Markdown emphasis markers.
            clean_explanation = clean_explanation.replace("**", "")
            clean_explanation = clean_explanation.replace("__", "")
            clean_explanation = clean_explanation.replace("*", "")
            clean_explanation = clean_explanation.replace("_", "")

            # Normalize list markers.
            clean_explanation = re.sub(
                r"(?m)^\s*[-•]\s+",
                "• ",
                clean_explanation,
            )
            clean_explanation = re.sub(
                r"(?m)^\s*\d+[.)]\s+",
                "• ",
                clean_explanation,
            )

            clean_explanation = re.sub(
                r"\n{3,}",
                "\n\n",
                clean_explanation,
            ).strip()

            # Avoid an overly long AI section.
            max_chars = 1800

            if len(clean_explanation) > max_chars:
                shortened = clean_explanation[:max_chars]
                clean_explanation = shortened.rsplit(" ", 1)[0] + "…"

                st.info(
                    "The AI interpretation is shortened for readability. "
                    "Review the findings below for the complete evidence."
                )

            # Use Streamlit Markdown instead of manually building HTML.
            st.markdown(clean_explanation)

        else:
            st.info(
                "No AI interpretation was returned. "
                "Review the calculated findings below."
            )

        st.divider()

        # RECOMMENDED ACTIONS
        st.markdown("### 🎯 Recommended Actions")
        st.caption(
            "Expand a finding to inspect its evidence, interpretation, "
            "suggested action, and limitations."
        )

        if not recommendations:
            st.info("No recommendations were returned.")
        else:
            for index, item in enumerate(recommendations, start=1):
                title = item.get("title", f"Finding {index}")

                severity = item.get(
                    "severity",
                    item.get("priority", "Informational"),
                )

                with st.expander(
                    f"{index}. {title} · {severity}",
                    expanded=False,
                ):
                    st.markdown("**📊 Supporting Evidence**")

                    evidence = item.get(
                        "evidence",
                        "No evidence available.",
                    )

                    # Remove stray backticks from older evidence strings.
                    if isinstance(evidence, str):
                        evidence = evidence.replace("`", "")

                    st.write(evidence)

                    st.markdown("**🔎 Interpretation**")
                    st.write(
                        item.get(
                            "interpretation",
                            "No interpretation available.",
                        )
                    )

                    st.markdown("**✅ Suggested Action**")
                    st.write(
                        item.get(
                            "action",
                            item.get(
                                "recommendation",
                                "No action available.",
                            ),
                        )
                    )

                    limitations = item.get("limitations")

                    if limitations:
                        st.markdown("**⚠️ Limitations**")
                        st.caption(limitations)

        st.caption(
            "Methodology: findings are calculated from observed data. "
            "Priority labels are rule-based and have not been statistically "
            "validated. Associations do not establish causation."
        )

        # COMPLETE VERIFIED ANALYSIS
        with st.expander("📄 View Complete Verified Analysis"):
            st.text(
                result.get(
                    "summary",
                    "No summary available.",
                )
            )

    else:
        st.info(
            "Click **Generate Business Recommendations** to analyze "
            "your sales data and view suggested actions."
        )


# --------------------------------------------------
# TAB 6 — DATA QUALITY
# --------------------------------------------------

with tab_quality:
    st.subheader("🔍 Data Quality & Validation")
    st.caption(
        "Monitor dataset completeness, consistency, and validation results."
    )

    if sales_df.empty:
        st.error("Cleaned dataset could not be loaded.")
    else:
        row_count = len(sales_df)
        column_count = len(sales_df.columns)
        missing_count = int(sales_df.isna().sum().sum())
        duplicate_count = int(sales_df.duplicated().sum())

        product_id_col = find_column(
            sales_df, "product_id", "productid"
        )
        product_name_col = find_column(
            sales_df, "product_name", "productname"
        )
        category_col = find_column(sales_df, "category")
        subcategory_col = find_column(
            sales_df, "sub_category", "subcategory"
        )
        profit_col = find_column(sales_df, "profit")

        inconsistent_product_ids = 0
        inconsistent_categories = 0
        inconsistent_subcategories = 0
        negative_profit_count = 0

        if product_id_col and product_name_col:
            names_per_id = sales_df.groupby(product_id_col)[
                product_name_col
            ].nunique()
            inconsistent_product_ids = int((names_per_id > 1).sum())

        if product_id_col and category_col:
            categories_per_id = sales_df.groupby(product_id_col)[
                category_col
            ].nunique()
            inconsistent_categories = int((categories_per_id > 1).sum())

        if product_id_col and subcategory_col:
            subcategories_per_id = sales_df.groupby(product_id_col)[
                subcategory_col
            ].nunique()
            inconsistent_subcategories = int(
                (subcategories_per_id > 1).sum()
            )

        if profit_col:
            profit_values = pd.to_numeric(
                sales_df[profit_col], errors="coerce"
            )
            negative_profit_count = int((profit_values < 0).sum())

        q1, q2, q3, q4 = st.columns(4)

        q1.metric("Total Records", f"{row_count:,}")
        q2.metric("Columns", f"{column_count}")
        q3.metric("Missing Cells", f"{missing_count:,}")
        q4.metric("Exact Duplicate Rows", f"{duplicate_count:,}")

        st.divider()
        st.markdown("### Validation Results")

        validation_rows = [
            {
                "Validation": "Missing values",
                "Result": "PASS" if missing_count == 0 else "REVIEW",
                "Details": f"{missing_count:,} missing cells",
            },
            {
                "Validation": "Exact duplicate rows",
                "Result": "PASS" if duplicate_count == 0 else "REVIEW",
                "Details": f"{duplicate_count:,} duplicate rows",
            },
            {
                "Validation": "Product ID → product name",
                "Result": (
                    "REVIEW" if inconsistent_product_ids else "PASS"
                ),
                "Details": (
                    f"{inconsistent_product_ids:,} IDs map to multiple names"
                ),
            },
            {
                "Validation": "Product ID → category",
                "Result": (
                    "PASS" if inconsistent_categories == 0 else "REVIEW"
                ),
                "Details": (
                    f"{inconsistent_categories:,} inconsistent IDs"
                ),
            },
            {
                "Validation": "Product ID → subcategory",
                "Result": (
                    "PASS" if inconsistent_subcategories == 0 else "REVIEW"
                ),
                "Details": (
                    f"{inconsistent_subcategories:,} inconsistent IDs"
                ),
            },
            {
                "Validation": "Negative-profit records",
                "Result": "INFO",
                "Details": (
                    f"{negative_profit_count:,} records with negative profit; "
                    "these may represent genuine losses"
                ),
            },
        ]

        validation_df = pd.DataFrame(validation_rows)

        st.dataframe(
            validation_df,
            width="stretch",
            hide_index=True,
        )

        st.divider()
        st.markdown("### Source Data Verification")

        st.success(
            "Previously verified: original Excel and cleaned CSV both "
            "contain 10,194 rows, with zero cell differences."
        )

        st.info(
            "The 32 product-name mapping inconsistencies were also present "
            "in the original source. They were not introduced by cleaning."
        )

        st.caption(
            "Negative profit is not automatically a data-quality error. "
            "This page recalculates checks from the loaded CSV; source "
            "comparison results are based on your previously run validation."
        )


# --------------------------------------------------
# 10. FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    f"""
    <div style="text-align:center; color:{C["muted"]}; font-size:12px;">
        TableauPulse · Python · MySQL · Streamlit · Plotly · Ollama
        <br>
        Retail Sales Intelligence Dashboard
    </div>
    """,
    unsafe_allow_html=True,
)
