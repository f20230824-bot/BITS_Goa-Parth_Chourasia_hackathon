"""Dashboard for the simulated sentiment-driven stock index."""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from joblib import load

from src.portfolio import calculate_weights, load_index
from src.risk_engine import enrich
from src.train_sentiment import score_records


DATA_DIR = Path(__file__).resolve().parent / "data"
HISTORY_FILE = DATA_DIR / "weight_history.csv"
FINAL_FILE = DATA_DIR / "rebalanced_index.csv"
RISK_FILE = DATA_DIR / "risk_signals.jsonl"
INDEX_FILE = DATA_DIR / "index.csv"
MODEL_FILE = DATA_DIR / "sentiment_model.joblib"


@st.cache_resource
def load_fitted_model(path, modified_ns):
    """Reload a model when the training script replaces its local artifact."""
    return load(path)

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

st.subheader("Analyze a new text item")
st.caption("Paste a public headline or post and choose its company. This what-if result is not saved.")
with st.form("new_signal"):
    chosen_ticker = st.selectbox("Company ticker", final["ticker"].tolist())
    input_source = st.selectbox("Text source", ["News headline", "Social post"])
    input_text = st.text_area("Headline or post text", max_chars=1000)
    submitted = st.form_submit_button("Analyze and simulate")

if submitted:
    if not input_text.strip():
        st.warning("Enter a headline or post first.")
    elif not MODEL_FILE.exists() or not RISK_FILE.exists():
        st.error("Run the preparation, training, and risk-engine commands before using the form.")
    else:
        model = load_fitted_model(str(MODEL_FILE), MODEL_FILE.stat().st_mtime_ns)
        source = "manual_social" if input_source == "Social post" else "manual_news"
        record = {"source": source, "ticker": chosen_ticker, "text": input_text.strip(),
                  "collection_method": "manual_demo", "url": ""}
        new_signal = enrich(score_records(model, [record])[0])
        with RISK_FILE.open(encoding="utf-8") as file:
            existing = [json.loads(line) for line in file if line.strip()]
        stocks = load_index(INDEX_FILE)
        before = {row["ticker"]: row for row in calculate_weights(stocks, existing)}
        after = {row["ticker"]: row for row in calculate_weights(stocks, existing + [new_signal])}
        st.write({
            "ticker": new_signal["ticker"],
            "sentiment": new_signal["sentiment_label"],
            "sentiment_score": new_signal["sentiment_score"],
            "event_type": new_signal["event_type"],
            "impact_score": new_signal["impact_score"],
            "matched_phrase": new_signal["event_evidence"],
        })
        if new_signal["event_type"] == "Other/Unclear":
            st.info("No recognized event: this item does not change the mock index.")
        comparison = pd.DataFrame([
            {
                "Ticker": ticker,
                "Before (%)": round(before[ticker]["new_weight"] * 100, 4),
                "After (%)": round(after[ticker]["new_weight"] * 100, 4),
                "Change (percentage points)": round(
                    (after[ticker]["new_weight"] - before[ticker]["new_weight"]) * 100, 4
                ),
            }
            for ticker in before
        ])
        st.dataframe(comparison, hide_index=True, width="stretch")
        st.caption("The simulation uses a social-post sentiment model and fixed weight rules; "
                   "it does not predict market returns.")

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
        "signal_count": "Signals used",
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
