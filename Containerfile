FROM docker.io/library/python:3.12-slim
WORKDIR /app
COPY requirements-bot.txt .
RUN pip install --no-cache-dir -r requirements-bot.txt
COPY bot.py store.py embeddings.py reactions.py retrieval.py api.py ./
ENV PYTHONUNBUFFERED=1 JOKER_STORE_DIR=/app/data/store
USER 1000:1000
CMD ["python", "bot.py"]
