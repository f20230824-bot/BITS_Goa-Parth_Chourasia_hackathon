"""Combine scored social and news text into machine-readable risk signals.

Event categories and impact scores are transparent rules for a prototype.
They have not been trained or validated against actual market outcomes.
"""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT = DATA_DIR / "risk_signals.jsonl"

# Ordered rules: more specific events take precedence over general earnings or
# product wording. The number is a starting severity on a 1-10 demo scale.
EVENT_RULES = [
    ("Credit Event", 8, r"\b(default|bankrupt\w*|insolven\w*|credit downgrade|debt restructuring)\b"),
    ("Geopolitical", 7, r"\b(war|sanction\w*|tariff\w*|trade ban|export control\w*)\b"),
    ("Regulatory", 6, r"\b(probe\w*|investigat\w*|antitrust|monopol\w*|lawsuit|sued|fine\w*|appeal\w*|regulator\w*)\b"),
    ("Merger/Acquisition", 6, r"\b(acqui\w*|merger|takeover|buyout)\b"),
    ("Earnings/Guidance", 5, r"\b(earnings|(?:first|second|third|fourth)[ -]quarter.{0,40}results|quarterly results|financial results|revenue|profit\w*|guidance|outlook|forecast\w*|capex|capital spending)\b"),
    ("Product Launch", 4, r"\b(unveil\w*|launch\w*|introduc\w*|new product|new device)\b"),
    ("Analyst Action", 3, r"\b(upgrad\w*|downgrad\w*|price target|analyst rating|overweight|underweight)\b"),
    ("Corporate Action", 3, r"\b(dividend\w*|repurchase\w*|buyback\w*|stock split)\b"),
]


def classify_event(text):
    for category, base_impact, pattern in EVENT_RULES:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return category, base_impact, match.group(0)
    return "Other/Unclear", 1, ""


def enrich(record):
    category, base_impact, evidence = classify_event(record["text"])
    sentiment = float(record["sentiment_score"])
    # Stronger model sentiment nudges a recognized event up by at most 2 points.
    # Unknown events remain at 1 because sentiment alone is not an event.
    adjustment = min(2, int(abs(sentiment) * 3)) if evidence else 0
    source_type = "social" if record["source"] == "historical_social" else "news"
    identity = f'{record["source"]}|{record["ticker"]}|{record["text"]}'
    return {
        **record,
        "signal_id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12],
        "source_type": source_type,
        "event_type": category,
        "event_evidence": evidence,
        "impact_score": min(10, base_impact + adjustment),
        "impact_method": "rule_based_v1",
    }


def load_jsonl(path):
    if not path.exists():
        raise SystemExit(f"Missing {path.name}; run the preparation and training steps first.")
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def main():
    social = load_jsonl(DATA_DIR / "social_signals.jsonl")
    news = load_jsonl(DATA_DIR / "news_signals.jsonl")
    signals = [enrich(record) for record in social + news]
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in signals),
        encoding="utf-8",
    )
    print(f"Saved {len(signals)} risk signals to {OUTPUT}")
    print("Sources:", dict(Counter(row["source_type"] for row in signals)))
    print("Events:", dict(Counter(row["event_type"] for row in signals)))


if __name__ == "__main__":
    main()
