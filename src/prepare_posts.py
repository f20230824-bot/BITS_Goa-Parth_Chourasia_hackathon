"""Prepare historical social posts and optional cached public Bluesky posts."""

import argparse
import csv
import json
import re
from pathlib import Path

from social_filter import focused_on


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--include-cached", action="store_true",
                    help="also include posts cached by ingest_bluesky.py")
args = parser.parse_args()

with (DATA_DIR / "index.csv").open(newline="", encoding="utf-8") as file:
    tickers = {row["ticker"] for row in csv.DictReader(file)}

records = []
seen = set()


def add_record(ticker, text, source, **metadata):
    text = text.strip()
    if ticker not in tickers or not re.search(
        rf"(?<!\w)\${re.escape(ticker)}\b", text, re.IGNORECASE
    ):
        return
    if source == "bluesky_social" and not focused_on(ticker, text):
        return
    key = (source, ticker, text.casefold())
    if key in seen:
        return
    seen.add(key)
    records.append({"source": source, "ticker": ticker, "text": text, **metadata})


with (DATA_DIR / "social_posts.csv").open(newline="", encoding="utf-8") as file:
    for source_index, row in enumerate(csv.DictReader(file)):
        for ticker in sorted(tickers):
            add_record(ticker, row["text"], "historical_social",
                       source_index=source_index, collection_method="historical_dataset",
                       source_kind="historical_social", url="")

cache = DATA_DIR / "bluesky_posts.json"
if args.include_cached and cache.exists():
    for post in json.loads(cache.read_text(encoding="utf-8")):
        if post.get("url", "").startswith("https://bsky.app/"):
            add_record(post.get("ticker", ""), post.get("text", ""),
                       "bluesky_social", url=post["url"],
                       seen_date=post.get("published", ""),
                       collection_method="bluesky_search", source_kind="public_social")

output = DATA_DIR / "social_inputs.jsonl"
output.write_text(
    "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
    encoding="utf-8",
)
print(f"Saved {len(records)} candidate stock-post matches to {output}")
print(f"Historical: {sum(r['source'] == 'historical_social' for r in records)}; "
      f"Bluesky: {sum(r['source'] == 'bluesky_social' for r in records)}")
for record in records[:5]:
    print(record["ticker"], "-", record["text"][:100])
