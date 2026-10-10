"""Prepare source-linked news headlines for the risk engine."""

import csv
import json
import re
from pathlib import Path

data_dir = Path(__file__).resolve().parents[1] / "data"
articles_file = data_dir / "gdelt_articles.json"
seed_file = data_dir / "news_seed.csv"
output_file = data_dir / "news_inputs.jsonl"

aliases = {
    "AAPL": ["Apple"],
    "MSFT": ["Microsoft"],
    "AMZN": ["Amazon"],
    "GOOGL": ["Alphabet", "Google"],
    "META": ["Meta"],
    "NVDA": ["Nvidia"],
    "JPM": ["JPMorgan", "JP Morgan", "J.P. Morgan"],
    "JNJ": ["Johnson & Johnson", "J&J"],
    "XOM": ["Exxon", "Exxon Mobil", "ExxonMobil"],
    "WMT": ["Walmart"],
}

records = []
seen = set()

def add_record(ticker, title, url, seen_date, collection_method, source_kind):
    title = title.strip()
    url = url.strip()
    if ticker not in aliases or not title or not url.startswith("https://"):
        return
    if not any(
        re.search(r"\b" + re.escape(name) + r"\b", title, re.IGNORECASE)
        for name in aliases[ticker]
    ):
        return
    key = (url, ticker)
    if key in seen:
        return
    seen.add(key)
    records.append({
        "source": "news",
        "ticker": ticker,
        "text": title,
        "url": url,
        "seen_date": seen_date,
        "collection_method": collection_method,
        "source_kind": source_kind,
    })


# This reviewed, source-linked sample makes the demo reproducible when GDELT
# rate-limits live searches. Its texts are short paraphrases, not article bodies.
with seed_file.open(newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        add_record(
            row["ticker"], row["text"], row["url"], row["published_date"],
            "curated_sample", row["source_kind"]
        )

# Add any live GDELT headlines that clearly name an index company.
if articles_file.exists():
    articles = json.loads(articles_file.read_text(encoding="utf-8"))
    for article in articles:
        if article.get("language") != "English":
            continue
        title = article.get("title", "")
        for ticker in aliases:
            add_record(
                ticker, title, article.get("url", ""),
                article.get("seendate", ""), "gdelt", "independent_news"
            )

with output_file.open("w", encoding="utf-8") as file:
    for record in records:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

print(f"Saved {len(records)} relevant news records to {output_file}")
print(f"Curated: {sum(r['collection_method'] == 'curated_sample' for r in records)}; "
      f"GDELT: {sum(r['collection_method'] == 'gdelt' for r in records)}")
for record in records:
    print(record["ticker"], "-", record["text"])
