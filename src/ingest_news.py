import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Find the repository's data folder, regardless of where VS Code runs the script.
project_dir = Path(__file__).resolve().parents[1]
cache = project_dir / "data" / "gdelt_articles.json"

params = {
    "query": '"Apple" stock',
    "mode": "artlist",
    "format": "json",
    "timespan": "1week",
    "maxrecords": 20,
    "sort": "datedesc",
}
url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
request = Request(url, headers={"User-Agent": "HackathonRiskEngine/1.0"})

try:
    with urlopen(request, timeout=30) as response:
        articles = json.load(response).get("articles", [])

    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps(articles, indent=2), encoding="utf-8")
    print("Fetched fresh articles from GDELT.")

except HTTPError as error:
    if error.code != 429:
        raise

    if not cache.exists():
        raise SystemExit(
            "GDELT returned HTTP 429 (too many requests), and no saved data exists. "
            "Try again later."
        ) from error

    articles = json.loads(cache.read_text(encoding="utf-8"))
    print("GDELT returned HTTP 429; using saved articles.")

print(f"Available articles: {len(articles)}")
for article in articles[:5]:
    print("-", article.get("title", "(no title)"))