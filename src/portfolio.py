"""Shared, deterministic weight calculation for batch runs and the dashboard."""

import csv
from collections import defaultdict
from statistics import mean


ALPHA = 0.2  # Sensitivity chosen for the simulation, not estimated from returns.


def load_index(path):
    with path.open(newline="", encoding="utf-8") as file:
        stocks = list(csv.DictReader(file))
    if not stocks:
        raise ValueError("The mock index is empty")
    tickers = [stock["ticker"] for stock in stocks]
    if len(tickers) != len(set(tickers)):
        raise ValueError("The mock index contains duplicate tickers")
    weights = [float(stock["base_weight"]) for stock in stocks]
    if any(weight <= 0 for weight in weights) or abs(sum(weights) - 1.0) > 1e-6:
        raise ValueError("Starting index weights must be positive and add up to 1.0")
    return stocks


def calculate_weights(stocks, signals, alpha=ALPHA):
    """Transfer weight from negative to positive eligible sentiment.

    Unknown events and unknown tickers cannot change the mock index. If the
    eligible sentiment has only one sign, there is no opposite side to fund a
    transfer, so all starting weights are retained.
    """
    scores = defaultdict(list)
    tickers = {stock["ticker"] for stock in stocks}
    for signal in signals:
        if signal["event_type"] == "Other/Unclear" or signal["ticker"] not in tickers:
            continue
        score = float(signal["sentiment_score"])
        if not -1 <= score <= 1:
            raise ValueError("Sentiment scores must be between -1 and 1")
        scores[signal["ticker"]].append(score)

    rows = []
    for stock in stocks:
        ticker = stock["ticker"]
        base = float(stock["base_weight"])
        average = mean(scores[ticker]) if scores[ticker] else 0.0
        rows.append({
            "ticker": ticker,
            "company": stock["company"],
            "base_weight": base,
            "signal_count": len(scores[ticker]),
            "average_sentiment": average,
            "desired_change": alpha * base * average,
        })

    positive = sum(max(row["desired_change"], 0) for row in rows)
    negative = sum(max(-row["desired_change"], 0) for row in rows)
    transfer = min(positive, negative)
    for row in rows:
        desired = row["desired_change"]
        if desired > 0 and positive:
            change = transfer * desired / positive
        elif desired < 0 and negative:
            change = transfer * desired / negative
        else:
            change = 0.0
        row["new_weight"] = row["base_weight"] + change
    return rows
