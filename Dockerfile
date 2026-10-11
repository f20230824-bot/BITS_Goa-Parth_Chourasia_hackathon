FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/
COPY app.py ./
COPY data/index.csv data/social_train.csv data/social_posts.csv data/news_seed.csv ./data/

# Generate the model and replay artifacts from the tracked demo inputs.
# Live feeds and credentials are not needed to run the built image.
RUN python src/run_pipeline.py
RUN python -m unittest discover -s tests

RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" || exit 1
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
