"""Cache recent public Bluesky posts with explicit index-company cashtags."""

import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from social_filter import focused_on


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT = DATA_DIR / "bluesky_posts.json"
API = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"


def fetch_ticker(ticker):
    url = API + "?" + urlencode({"q": "$" + ticker, "sort": "latest", "limit": 25, "lang": "en"})
    request = Request(url, headers={"User-Agent": "HackathonRiskEngine/1.0"})
    with urlopen(request, timeout=12) as response:
        payload = json.load(response)

    records = []
    for post in payload.get("posts", []):
        body = post.get("record", {})
        text = body.get("text", "").strip()
        langs = body.get("langs", [])
        if langs and "en" not in langs:
            continue
        if not focused_on(ticker, text):
            continue
        uri = post.get("uri", "")
        handle = post.get("author", {}).get("handle", "")
        if not uri.startswith("at://") or not handle:
            continue
        records.append({
            "ticker": ticker,
            "text": text,
            "url": f"https://bsky.app/profile/{handle}/post/{uri.rsplit('/', 1)[-1]}",
            "published": body.get("createdAt", ""),
        })
    return records


def main():
    with (DATA_DIR / "index.csv").open(newline="", encoding="utf-8") as file:
        tickers = [row["ticker"] for row in csv.DictReader(file)]
    posts = []
    for ticker in tickers:
        try:
            fresh = fetch_ticker(ticker)
            posts.extend(fresh)
            print(f"{ticker}: {len(fresh)} exact-cashtag posts")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"{ticker}: unavailable ({error})")
        time.sleep(0.15)

    if not posts:
        print("No new posts; existing cache, if any, was left untouched.")
        return
    OUTPUT.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(posts)} posts to {OUTPUT}")


if __name__ == "__main__":
    main()
