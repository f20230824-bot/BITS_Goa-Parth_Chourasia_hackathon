import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

data_dir = Path(__file__).resolve().parents[1] / "data"
alpha = 0.2

with (data_dir / "index.csv").open(newline="", encoding="utf-8") as file:
    stocks = list(csv.DictReader(file))

with (data_dir / "social_signals.jsonl").open(encoding="utf-8") as file:
    signals = [json.loads(line) for line in file if line.strip()]

scores = defaultdict(list)
output = data_dir / "weight_history.csv"

with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["step", "ticker", "company", "weight", "signal_count"])

    # Step 0 is the starting index. Each later step includes one more post.
    for step in range(len(signals) + 1):
        if step > 0:
            signal = signals[step - 1]
            scores[signal["ticker"]].append(float(signal["sentiment_score"]))

        rows = []
        for stock in stocks:
            ticker = stock["ticker"]
            base = float(stock["base_weight"])
            average = mean(scores[ticker]) if scores[ticker] else 0.0
            rows.append({
                "ticker": ticker,
                "company": stock["company"],
                "base": base,
                "count": len(scores[ticker]),
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

            writer.writerow([
                step,
                row["ticker"],
                row["company"],
                f'{row["base"] + change:.10f}',
                row["count"],
            ])

print(f"Saved {len(signals) + 1} simulation steps to {output}")