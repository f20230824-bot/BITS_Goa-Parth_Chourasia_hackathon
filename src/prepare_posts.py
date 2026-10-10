import csv
import json
import re
from pathlib import Path

project_dir = Path(__file__).resolve().parents[1]
data_dir = project_dir / "data"

aliases = {
    "AAPL": ["Apple", "iPhone"],
    "MSFT": ["Microsoft"],
    "AMZN": ["Amazon"],
    "GOOGL": ["Google", "Alphabet"],
    "META": ["Meta", "Facebook"],
    "NVDA": ["Nvidia"],
    "JPM": ["JPMorgan", "JP Morgan"],
    "JNJ": ["Johnson & Johnson", "J&J"],
    "XOM": ["Exxon"],
    "WMT": ["Walmart"],
}

with (data_dir / "index.csv").open(newline="", encoding="utf-8") as file:
    tickers = [row["ticker"] for row in csv.DictReader(file)]

records = []
with (data_dir / "social_posts.csv").open(newline="", encoding="utf-8") as file:
    for source_index, row in enumerate(csv.DictReader(file)):
        text = row["text"].strip()
        if not text:
            continue

        for ticker in tickers:
            cashtag = re.search(
                rf"(?<!\w)\${re.escape(ticker)}\b", text, re.IGNORECASE
            )
            name = any(
                re.search(rf"\b{re.escape(alias)}\b", text, re.IGNORECASE)
                for alias in aliases[ticker]
            )

            if cashtag or name:
                records.append({
                    "source": "historical_social",
                    "source_index": source_index,
                    "ticker": ticker,
                    "text": text,
                })

output = data_dir / "social_inputs.jsonl"
output.write_text(
    "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
    encoding="utf-8",
)

print(f"Saved {len(records)} candidate stock-post matches to {output}")
for record in records[:5]:
    print(record["ticker"], "-", record["text"][:100])