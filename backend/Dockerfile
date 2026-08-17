FROM python:3.12-slim

# Log non bufferati e nessun .pyc: entrambi indesiderati in container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# libpq è richiesta a runtime da psycopg.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiate per prime: il layer di pip resta in cache finché non cambiano.
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .

# Utente non privilegiato: un processo compromesso non deve essere root.
RUN useradd --create-home --uid 1000 askyvet \
    && chown -R askyvet:askyvet /app
USER askyvet

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
