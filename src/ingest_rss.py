"""Fetch current headlines from official company newsroom RSS/Atom feeds.

This is an optional refresh. The source-linked news seed keeps the demo usable
without internet access. Only headline metadata is stored, not article bodies.
"""

import json
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT = DATA_DIR / "rss_articles.json"
ATOM = "{http://www.w3.org/2005/Atom}"
FEEDS = {
    "AAPL": "https://www.apple.com/newsroom/rss-feed.rss",
    "MSFT": "https://news.microsoft.com/source/feed/",
    "AMZN": "https://www.aboutamazon.com/rss/feed.rss",
    "GOOGL": "https://blog.google/rss/",
    "META": "https://about.fb.com/news/feed/",
}


def parse_feed(xml_bytes, ticker):
    root = ET.fromstring(xml_bytes)
    if root.tag == ATOM + "feed":
        items = root.findall(ATOM + "entry")
        def fields(item):
            link = item.find(ATOM + "link")
            return (
                item.findtext(ATOM + "title", default=""),
                link.get("href", "") if link is not None else "",
                item.findtext(ATOM + "updated", default=""),
            )
    elif root.tag == "rss":
        items = root.findall("./channel/item")
        def fields(item):
            return (
                item.findtext("title", default=""),
                item.findtext("link", default=""),
                item.findtext("pubDate", default=""),
            )
    else:
        raise ValueError(f"Unsupported feed format: {root.tag}")

    articles = []
    for item in items:
        title, url, published = fields(item)
        if title.strip() and url.strip().startswith("https://"):
            articles.append({
                "ticker": ticker,
                "title": " ".join(title.split()),
                "url": url.strip(),
                "published": published.strip(),
            })
    return articles


def main():
    articles = []
    for ticker, url in FEEDS.items():
        try:
            request = Request(url, headers={"User-Agent": "HackathonRiskEngine/1.0"})
            with urlopen(request, timeout=12) as response:
                xml_bytes = response.read(1_000_001)
            if len(xml_bytes) > 1_000_000:
                raise ValueError("Feed exceeds 1 MB limit")
            fresh = parse_feed(xml_bytes, ticker)
            print(f"{ticker}: {len(fresh)} headlines")
            articles.extend(fresh)
        except (OSError, ValueError, ET.ParseError) as error:
            print(f"{ticker}: unavailable ({error})")

    if not articles:
        print("No new feed data; existing cache, if any, was left untouched.")
        return
    OUTPUT.write_text(json.dumps(articles, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(articles)} headlines to {OUTPUT}")


if __name__ == "__main__":
    main()
