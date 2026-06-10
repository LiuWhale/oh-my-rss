FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

ENTRYPOINT ["oh-my-rss"]
