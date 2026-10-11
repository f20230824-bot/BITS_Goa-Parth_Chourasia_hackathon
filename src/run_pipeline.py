"""Generate the reproducible demo artifacts using the current interpreter."""

import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
STEPS = (
    "prepare_posts.py",
    "prepare_news.py",
    "train_sentiment.py",
    "risk_engine.py",
    "rebalance.py",
    "rebalance_history.py",
)


def main():
    for step in STEPS:
        print(f"Running {step}", flush=True)
        subprocess.run(
            [sys.executable, str(PROJECT_DIR / "src" / step)],
            cwd=PROJECT_DIR,
            check=True,
        )


if __name__ == "__main__":
    main()
