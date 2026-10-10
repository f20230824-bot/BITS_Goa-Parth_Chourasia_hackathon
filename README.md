# BITS_Goa-Parth_Chourasia_hackathon

This project analyzes financial news and public social posts to identify risks affecting companies. The planned risk engine will produce a sentiment score, event category, and impact score for each item. Module A will use sentiment to adjust the weights of a mock stock index and show the changes over time.

## Current prototype

- `data/index.csv` defines a mock index of ten stocks with equal starting weights.
- `src/ingest_news.py` fetches recent GDELT article metadata. GDELT may rate limit requests; the script can use a locally saved response.
- `src/prepare_posts.py` selects historical social posts with explicit `$TICKER` mentions. This conservative match avoids treating an analyst's company as the subject of a post.
- `src/train_sentiment.py` trains a TF-IDF and logistic regression sentiment baseline, evaluates it on held-out posts, and scores the matched posts.
- `src/rebalance.py` uses those sentiment scores to adjust a mock index and writes `data/rebalanced_index.csv`.
- `src/rebalance_history.py` replays scored posts as simulation steps and writes `data/weight_history.csv`.
- `app.py` displays the changing weights and the final index in a Streamlit dashboard.

## Run the prototype

Use Python 3.11. From the repository root, run:

```bash
python3 -m pip install -r requirements.txt
python3 src/prepare_posts.py
python3 src/train_sentiment.py
python3 src/rebalance.py
python3 src/rebalance_history.py
python3 -m streamlit run app.py
```

The training command writes `data/social_signals.jsonl`. Each record includes a sentiment label and a score from -1 to 1, calculated as `P(bullish) - P(bearish)`. The model does not read the source sentiment labels when scoring these records.

The rebalancer writes `data/rebalanced_index.csv`. It transfers weight from stocks with negative average sentiment to stocks with positive average sentiment, in proportion to their desired changes. Stocks with no sentiment signal keep their starting weight. If all available signals have the same sign, it makes no transfer because there is no opposite side to fund it. The `alpha = 0.2` sensitivity is a simulation assumption, not an estimated market effect.

The history script writes one index snapshot before any post and one after each scored post. The source data has no timestamps, so the dashboard's horizontal axis represents simulation steps rather than real time.

The social data comes from the [Twitter Financial News Sentiment dataset](https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment) (MIT license). `data/social_train.csv` is the training split and `data/social_posts.csv` is the validation split, replayed as historical posts rather than live social data. The dataset maps 0 to bearish, 1 to bullish, and 2 to neutral. Before training, the script excludes training rows whose cleaned text also appears in validation.

On the 2,388-row validation file, this baseline reached 0.802 accuracy and 0.744 macro F1 after excluding 68 overlapping training rows. These are sentiment classification results, not evidence of profitable index rebalancing.

## Next components

The prototype still needs company attribution for name-only mentions, event classification, and impact scoring. The current GDELT response is noisy and needs better filtering before it is used as a second production-quality input.
