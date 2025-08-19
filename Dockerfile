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

# Copier les dépendances depuis builder
COPY --from=builder /root/.local /root/.local

# Mettre pip packages dans le PATH
ENV PATH=/root/.local/bin:$PATH

# Créer les dossiers nécessaires
RUN mkdir -p /app/vector_db /app/data/cgi_documents

# Copier code source
COPY app/ ./app/
COPY static/ ./static/
COPY data/ ./data/

# ✅ CORRECTION : S'assurer que le répertoire cgi_documents existe
RUN mkdir -p /app/data/cgi_documents

# Exposer port
EXPOSE 8000

# ✅ SOLUTION : Utiliser uvicorn au lieu de gunicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]






















# # ========================
# # Étape 1 : Build
# # ========================
# FROM python:3.11-slim AS builder

# WORKDIR /app

# # Installer dépendances système nécessaires uniquement pour compiler
# RUN apt-get update && apt-get install -y gcc build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Copier requirements
# COPY requirements.simple.txt .

# # Installer dépendances dans un dossier séparé
# RUN pip install --no-cache-dir --user -r requirements.simple.txt


# # ========================
# # Étape 2 : Runtime (image finale, plus légère)
# # ========================
# FROM python:3.11-slim

# WORKDIR /app

# # Copier les dépendances depuis builder
# COPY --from=builder /root/.local /root/.local

# # Mettre pip packages dans le PATH
# ENV PATH=/root/.local/bin:$PATH

# # Créer dossier vector_db avec bons droits
# RUN mkdir -p /app/vector_db

# # Copier code source
# COPY app/ ./app/
# COPY static/ ./static/
# COPY data/ ./data/

# # ✅ CORRECTION : Créer le répertoire cgi_documents s'il n'existe pas
# RUN mkdir -p /app/data/cgi_documents

# # Exposer port
# EXPOSE 8000

# # ✅ SOLUTION SIMPLE : Rester en root, ajouter gunicorn aux requirements
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-w", "4", "-b", "0.0.0.0:8000"]