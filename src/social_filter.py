"""Conservative company attribution for current public social posts."""

import re


ISSUER_NAMES = {
    "AAPL": ("Apple",),
    "MSFT": ("Microsoft",),
    "AMZN": ("Amazon",),
    "GOOGL": ("Google", "Alphabet"),
    "META": ("Meta",),
    "NVDA": ("Nvidia",),
    "JPM": ("JPMorgan", "JP Morgan", "J.P. Morgan"),
    "JNJ": ("Johnson & Johnson", "J&J"),
    "XOM": ("Exxon", "ExxonMobil"),
    "WMT": ("Walmart",),
}


def focused_on(ticker, text):
    """Require one cashtag and an explicit issuer name in the same post.

    This sacrifices recall to avoid attributing a news roundup about a
    different company to every stock casually tagged at its end.
    """
    if ticker not in ISSUER_NAMES:
        return False
    cashtags = {tag.upper() for tag in re.findall(r"(?<!\w)\$[A-Za-z]{1,6}\b", text)}
    if cashtags != {"$" + ticker}:
        return False
    return any(
        re.search(r"\b" + re.escape(name) + r"\b", text, re.IGNORECASE)
        for name in ISSUER_NAMES[ticker]
    )
