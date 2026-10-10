"""Replay eligible signals in file order to show simulated index history."""

import csv
import json
from pathlib import Path

from portfolio import calculate_weights, load_index


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main():
    stocks = load_index(DATA_DIR / "index.csv")
    with (DATA_DIR / "risk_signals.jsonl").open(encoding="utf-8") as file:
        signals = [
            signal for line in file if line.strip()
            if (signal := json.loads(line))["event_type"] != "Other/Unclear"
        ]

    output = DATA_DIR / "weight_history.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["step", "ticker", "company", "weight", "signal_count"])
        for step in range(len(signals) + 1):
            for row in calculate_weights(stocks, signals[:step]):
                writer.writerow([
                    step, row["ticker"], row["company"],
                    f'{row["new_weight"]:.10f}', row["signal_count"],
                ])

    print(f"Saved {len(signals) + 1} simulation steps to {output}")


if __name__ == "__main__":
    main()
