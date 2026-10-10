"""Dashboard for the simulated sentiment-driven stock index."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).resolve().parent / "data"
HISTORY_FILE = DATA_DIR / "weight_history.csv"
FINAL_FILE = DATA_DIR / "rebalanced_index.csv"
RISK_FILE = DATA_DIR / "risk_signals.jsonl"

st.set_page_config(page_title="Mock Index Rebalancing", layout="wide")
st.title("Sentiment-driven mock index")
st.caption(
    "Historical social posts and source-linked news are replayed in file order as simulation steps. "
    "The steps are not real-world timestamps or investment recommendations."
)

if not HISTORY_FILE.exists() or not FINAL_FILE.exists():
    st.error("Generate the index data before opening the dashboard.")
    st.code(
        "python3 src/prepare_posts.py\n"
        "python3 src/prepare_news.py\n"
        "python3 src/train_sentiment.py\n"
        "python3 src/risk_engine.py\n"
        "python3 src/rebalance.py\n"
        "python3 src/rebalance_history.py",
        language="bash",
    )
    st.stop()

history = pd.read_csv(HISTORY_FILE)
final = pd.read_csv(FINAL_FILE)

tickers = sorted(history["ticker"].unique())
selected = st.multiselect(
    "Stocks to display",
    tickers,
    default=[ticker for ticker in ("AAPL", "JPM", "MSFT") if ticker in tickers],
)

st.subheader("Index weight by simulation step")
st.caption("Module A uses sentiment from signals with a recognized event type.")
if selected:
    chart_data = history[history["ticker"].isin(selected)].copy()
    chart_data["weight_pct"] = chart_data["weight"] * 100
    low = chart_data["weight_pct"].min()
    high = chart_data["weight_pct"].max()
    padding = max((high - low) * 0.1, 0.05)
    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("step:Q", title="Simulation step", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y(
                "weight_pct:Q",
                title="Index weight (%)",
                scale=alt.Scale(domain=[low - padding, high + padding], zero=False),
            ),
            color=alt.Color("ticker:N", title="Stock"),
            tooltip=[
                alt.Tooltip("step:Q", title="Step"),
                alt.Tooltip("ticker:N", title="Stock"),
                alt.Tooltip("weight_pct:Q", title="Weight (%)", format=".4f"),
            ],
        )
        .properties(height=380)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("The vertical axis is zoomed to show small weight changes; hover for exact values.")
else:
    st.info("Select at least one stock to display its weight history.")

st.subheader("Final weights")
table = final[
    ["ticker", "company", "base_weight", "new_weight", "change_pp", "signal_count"]
].copy()
table["base_weight"] *= 100
table["new_weight"] *= 100
table = table.rename(
    columns={
        "ticker": "Ticker",
        "company": "Company",
        "base_weight": "Starting weight (%)",
        "new_weight": "Final weight (%)",
        "change_pp": "Change (percentage points)",
        "signal_count": "Posts scored",
    }
)
st.dataframe(table, hide_index=True, width="stretch")

st.subheader("Structured risk signals")
st.caption(
    "Sentiment comes from the social-post model. Event labels and 1–10 impact "
    "scores use transparent rules; the impact scores are not market-validated predictions."
)
if RISK_FILE.exists():
    risks = pd.read_json(RISK_FILE, lines=True)
    source_filter = st.selectbox("Signal source", ["All", "News", "Social"])
    if source_filter != "All":
        risks = risks[risks["source_type"] == source_filter.lower()]
    risks = risks.sort_values("impact_score", ascending=False)
    risk_table = risks[
        ["source_type", "ticker", "text", "sentiment_score", "event_type",
         "impact_score", "event_evidence", "url"]
    ].rename(columns={
        "source_type": "Source",
        "ticker": "Ticker",
        "text": "Text",
        "sentiment_score": "Sentiment (-1 to 1)",
        "event_type": "Event",
        "impact_score": "Impact (1 to 10)",
        "event_evidence": "Matched phrase",
        "url": "Source link",
    })
    st.dataframe(
        risk_table, hide_index=True, width="stretch",
        column_config={"Source link": st.column_config.LinkColumn("Source link")},
    )
else:
    st.info("Run python3 src/risk_engine.py to display structured signals here.")
