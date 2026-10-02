FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg (Postgres driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run migrations, then start the server. On a free-tier host that sleeps,
# this means every cold start re-checks the schema is current before
# serving traffic — cheap insurance, migrations are idempotent no-ops
# once applied.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
