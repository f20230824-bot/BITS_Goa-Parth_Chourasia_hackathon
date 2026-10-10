# BITS_Goa-Parth_Chourasia_hackathon

This project analyzes financial news and public social posts to identify risks affecting companies. The planned risk engine will produce a sentiment score, event category, and impact score for each item. Module A will use sentiment to adjust the weights of a mock stock index and show the changes over time.

## Current prototype

- `data/index.csv` defines a mock index of ten stocks with equal starting weights.
- `src/ingest_news.py` fetches recent GDELT article metadata. GDELT may rate limit requests; the script can use a locally saved response.
- `src/ingest_rss.py` optionally fetches current headlines from five official company newsroom feeds. `src/prepare_news.py` keeps only headlines that explicitly name their issuing company.
- `data/news_seed.csv` contains ten short, paraphrased, source-linked public news and release items for a reproducible demo. `src/prepare_news.py` also adds relevant English GDELT headlines when a cache is available.
- `src/prepare_posts.py` selects historical social posts with explicit `$TICKER` mentions. This conservative match avoids treating an analyst's company as the subject of a post.
- `src/train_sentiment.py` trains a TF-IDF and logistic regression sentiment baseline, evaluates it on held-out posts, and scores both social and news inputs.
- `src/risk_engine.py` combines scored inputs and adds a rule-based event type and potential-impact score.
- `src/rebalance.py` uses sentiment from structured signals with a recognized event type to adjust a mock index and writes `data/rebalanced_index.csv`.
- `src/rebalance_history.py` replays scored posts as simulation steps and writes `data/weight_history.csv`.
- `app.py` displays the changing weights and the final index in a Streamlit dashboard.

## Run the prototype

Use Python 3.11. From the repository root, run:

```bash
python3 -m pip install -r requirements.txt
python3 src/prepare_posts.py
python3 src/prepare_news.py
python3 src/train_sentiment.py
python3 src/risk_engine.py
python3 src/rebalance.py
python3 src/rebalance_history.py
python3 -m streamlit run app.py
```

The training command writes `data/social_signals.jsonl` and `data/news_signals.jsonl`. Each record includes a sentiment label and a score from -1 to 1, calculated as `P(bullish) - P(bearish)`. The model does not read the source sentiment labels when scoring social records. The validation result below applies to social posts only; news-headline accuracy has not been measured.

The risk engine writes `data/risk_signals.jsonl` with source, ticker, text, sentiment, event type, matched phrase, and a 1–10 impact score. Event categories use ordered keyword rules. The impact score starts from a fixed event-category severity and rises by at most two points for stronger sentiment. `Other/Unclear` receives 1. These are explicit prototype assumptions, not market-calibrated predictions. The dashboard displays the unified output and its source links.

A [20-signal manual review](docs/signal_review.md) found four clear event-label errors, which were used to tighten the event rules. It is a small sanity check, not a measured event-classification accuracy or an evaluation of the sentiment model on news headlines.

The rebalancer writes `data/rebalanced_index.csv`. It uses recognized-event signals from both news and social inputs, excluding `Other/Unclear`. It transfers weight from stocks with negative average sentiment to stocks with positive average sentiment, in proportion to their desired changes. Stocks with no eligible signal keep their starting weight. If all available signals have the same sign, it makes no transfer because there is no opposite side to fund it. The `alpha = 0.2` sensitivity is a simulation assumption, not an estimated market effect.

The history script writes one index snapshot before any eligible signal and one after each additional signal. Historical social posts lack timestamps and the two sources are replayed in file order, so the dashboard's horizontal axis represents simulation steps rather than real time.

The social data comes from the [Twitter Financial News Sentiment dataset](https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment) (MIT license). `data/social_train.csv` is the training split and `data/social_posts.csv` is the validation split, replayed as historical posts rather than live social data. The dataset maps 0 to bearish, 1 to bullish, and 2 to neutral. Before training, the script excludes training rows whose cleaned text also appears in validation. The news sample is historical too. Its CSV includes a direct public source URL for every paraphrased headline. For an optional live refresh, run `python3 src/ingest_rss.py` before `prepare_news.py`, then rerun the remaining pipeline commands. This caches headline metadata from Apple, Microsoft, Amazon, Google, and Meta's official feeds; the cache is local and is not committed. These items are company announcements, not independent reporting. `src/ingest_news.py` remains an optional GDELT path; [GDELT's DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) may return HTTP 429. The curated sample still works without either live source.

On the 2,388-row validation file, this baseline reached 0.802 accuracy and 0.744 macro F1 after excluding 68 overlapping training rows. These are sentiment classification results, not evidence of profitable index rebalancing.

## Next components

The prototype still needs broader evaluation of news sentiment, event classification, and impact scoring, plus stronger company attribution for ambiguous name-only mentions. Live GDELT coverage is rate-limited and its cached response can be noisy. Official newsroom feeds cover five of the ten index companies, and many headlines describe products or marketing rather than material financial events. The source-linked sample supports a reproducible demo.
