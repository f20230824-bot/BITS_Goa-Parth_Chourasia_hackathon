import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

data_dir = Path(__file__).resolve().parents[1] / "data"
alpha = 0.2  # Simulation assumption: desired change is up to 20% of base weight

with (data_dir / "index.csv").open(newline="", encoding="utf-8") as file:
    stocks = list(csv.DictReader(file))

if abs(sum(float(stock["base_weight"]) for stock in stocks) - 1.0) > 1e-6:
    raise ValueError("Starting index weights must add up to 1.0")

scores = defaultdict(list)
with (data_dir / "social_signals.jsonl").open(encoding="utf-8") as file:
    for line in file:
        signal = json.loads(line)
        scores[signal["ticker"]].append(float(signal["sentiment_score"]))

rows = []
for stock in stocks:
    ticker = stock["ticker"]
    base_weight = float(stock["base_weight"])
    average_sentiment = mean(scores[ticker]) if scores[ticker] else 0.0
    desired_change = alpha * base_weight * average_sentiment

    rows.append({
        "ticker": ticker,
        "company": stock["company"],
        "base_weight": base_weight,
        "signal_count": len(scores[ticker]),
        "average_sentiment": average_sentiment,
        "desired_change": desired_change,
    })

# Transfer weight from negative-sentiment stocks to positive-sentiment stocks.
# The smaller side limits the transfer, so neutral stocks keep their weights.
positive_total = sum(max(row["desired_change"], 0) for row in rows)
negative_total = sum(max(-row["desired_change"], 0) for row in rows)
transfer = min(positive_total, negative_total)

for row in rows:
    desired_change = row["desired_change"]
    if desired_change > 0 and positive_total:
        change = transfer * desired_change / positive_total
    elif desired_change < 0 and negative_total:
        change = transfer * desired_change / negative_total
    else:
        change = 0.0
    row["new_weight"] = row["base_weight"] + change

output = data_dir / "rebalanced_index.csv"
with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        "ticker", "company", "base_weight", "signal_count",
        "average_sentiment", "new_weight", "change_pp"
    ])

    for row in rows:
        new_weight = row["new_weight"]
        change_pp = (new_weight - row["base_weight"]) * 100

        writer.writerow([
            row["ticker"],
            row["company"],
            f'{row["base_weight"]:.6f}',
            row["signal_count"],
            f'{row["average_sentiment"]:.4f}',
            f"{new_weight:.10f}",
            f"{change_pp:.4f}",
        ])

print(f"Saved rebalanced index to {output}")
print(f"Total new weight: {sum(row['new_weight'] for row in rows):.6f}")
