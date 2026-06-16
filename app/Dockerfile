# =====================================================================
# Dockerfile — service `ingestor`
# Image Python légère qui exécute nos scripts d'ingestion
# Construit localement par `docker compose build`
# =====================================================================
FROM python:3.12-slim

# Évite que Python écrive des .pyc et bufferise stdout (logs en direct)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installer les dépendances en premier (cache Docker friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code applicatif
COPY . .

# Par défaut, exécute le pipeline complet (Postgres + Mongo)
CMD ["python", "run_all.py"]
