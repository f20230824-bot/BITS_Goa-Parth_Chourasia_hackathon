"""Write the final mock-index weights from structured risk signals."""

import csv
import json
from pathlib import Path

from portfolio import calculate_weights, load_index


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main():
    stocks = load_index(DATA_DIR / "index.csv")
    with (DATA_DIR / "risk_signals.jsonl").open(encoding="utf-8") as file:
        signals = [json.loads(line) for line in file if line.strip()]
    rows = calculate_weights(stocks, signals)

    output = DATA_DIR / "rebalanced_index.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "ticker", "company", "base_weight", "signal_count",
            "average_sentiment", "new_weight", "change_pp",
        ])
        for row in rows:
            writer.writerow([
                row["ticker"], row["company"],
                f'{row["base_weight"]:.6f}', row["signal_count"],
                f'{row["average_sentiment"]:.4f}',
                f'{row["new_weight"]:.10f}',
                f'{(row["new_weight"] - row["base_weight"]) * 100:.4f}',
            ])

    print(f"Saved rebalanced index to {output}")
    print(f"Total new weight: {sum(row['new_weight'] for row in rows):.6f}")


if __name__ == "__main__":
    main()
