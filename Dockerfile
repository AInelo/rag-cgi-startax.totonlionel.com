# ========================
# Étape 1 : Build
# ========================
FROM python:3.11-slim AS builder

WORKDIR /app

# Installer dépendances système nécessaires uniquement pour compiler
RUN apt-get update && apt-get install -y gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.simple.txt .

# Installer dépendances dans un dossier séparé
RUN pip install --no-cache-dir --user -r requirements.simple.txt


# ========================
# Étape 2 : Runtime (image finale, plus légère)
# ========================
FROM python:3.11-slim

WORKDIR /app

# Créer utilisateur non-root
RUN useradd -m -u 1000 app && chown -R app:app /app

# Copier les dépendances depuis builder
COPY --from=builder /root/.local /root/.local

# Mettre pip packages dans le PATH
ENV PATH=/root/.local/bin:$PATH

# Créer dossier vector_db avec bons droits
RUN mkdir -p /app/vector_db && chmod -R 755 /app/vector_db

# Copier code source
COPY app/ ./app/
COPY static/ ./static/
COPY data/ ./data/

# Changer d’utilisateur
USER app

# Exposer port
EXPOSE 8000

# Commande de démarrage (prod-ready avec 4 workers uvicorn)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
