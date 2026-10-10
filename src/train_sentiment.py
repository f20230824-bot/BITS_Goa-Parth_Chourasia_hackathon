"""Train a financial-post sentiment baseline and score social and news inputs."""

import csv
import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import make_pipeline

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
LABEL_NAMES = {0: "bearish", 1: "bullish", 2: "neutral"}


def clean_text(text):
    """Remove shortened links, which do not explain financial sentiment."""
    return re.sub(r"https?://\S+", "", text).strip()


def load_labeled_posts(path):
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    texts = [clean_text(row["text"]) for row in rows]
    labels = [int(row["label"]) for row in rows]
    return texts, labels


def main():
    train_texts, train_labels = load_labeled_posts(DATA_DIR / "social_train.csv")
    valid_texts, valid_labels = load_labeled_posts(DATA_DIR / "social_posts.csv")

    # The published splits contain some duplicate text. Keep validation text
    # entirely out of training so the evaluation reflects unseen posts.
    validation_texts = {text.casefold() for text in valid_texts}
    train_pairs = [
        (text, label)
        for text, label in zip(train_texts, train_labels)
        if text.casefold() not in validation_texts
    ]
    print(f"Excluded {len(train_texts) - len(train_pairs)} overlapping training rows")
    train_texts = [text for text, _ in train_pairs]
    train_labels = [label for _, label in train_pairs]

    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    )
    model.fit(train_texts, train_labels)

    predictions = model.predict(valid_texts)
    print(f"Validation accuracy: {accuracy_score(valid_labels, predictions):.3f}")
    print(f"Validation macro F1: {f1_score(valid_labels, predictions, average='macro'):.3f}")
    print(
        classification_report(
            valid_labels,
            predictions,
            labels=[0, 1, 2],
            target_names=[LABEL_NAMES[i] for i in [0, 1, 2]],
            zero_division=0,
        )
    )

    input_path = DATA_DIR / "social_inputs.jsonl"
    if not input_path.exists():
        raise SystemExit("Run python3 src/prepare_posts.py first.")
    with input_path.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]

    probabilities = model.predict_proba([clean_text(row["text"]) for row in records])
    class_ids = list(model.named_steps["logisticregression"].classes_)
    bearish_index = class_ids.index(0)
    bullish_index = class_ids.index(1)
    scored = []
    for record, probs in zip(records, probabilities):
        best_index = max(range(len(probs)), key=lambda index: probs[index])
        scored.append(
            {
                **record,
                "sentiment_label": LABEL_NAMES[class_ids[best_index]],
                "sentiment_score": round(float(probs[bullish_index] - probs[bearish_index]), 4),
                "model_probability": round(float(probs[best_index]), 4),
            }
        )

    output_path = DATA_DIR / "social_signals.jsonl"
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in scored),
        encoding="utf-8",
    )
    print(f"Saved {len(scored)} sentiment signals to {output_path}")
    for row in scored[:5]:
        print(row["ticker"], row["sentiment_label"], row["sentiment_score"])

    news_path = DATA_DIR / "news_inputs.jsonl"
    if not news_path.exists():
        print("No news inputs found; run python3 src/prepare_news.py to score news.")
        return

    with news_path.open(encoding="utf-8") as file:
        news_records = [json.loads(line) for line in file if line.strip()]

    news_scored = []
    if news_records:
        news_probabilities = model.predict_proba(
            [clean_text(row["text"]) for row in news_records]
        )
        for record, probs in zip(news_records, news_probabilities):
            best_index = max(range(len(probs)), key=lambda index: probs[index])
            news_scored.append(
                {
                    **record,
                    "sentiment_label": LABEL_NAMES[class_ids[best_index]],
                    "sentiment_score": round(
                        float(probs[bullish_index] - probs[bearish_index]), 4
                    ),
                    "model_probability": round(float(probs[best_index]), 4),
                }
            )

    news_output = DATA_DIR / "news_signals.jsonl"
    news_output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in news_scored),
        encoding="utf-8",
    )
    print(f"Saved {len(news_scored)} news sentiment signals to {news_output}")


if __name__ == "__main__":
    main()
