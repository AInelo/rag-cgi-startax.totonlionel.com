#!/bin/bash
set -euo pipefail

echo "📦 Génération du fichier .env.prod à partir des variables d'environnement..."

# === ✅ Vérification explicite de chaque variable ===

required_vars=(
  DEFAULT_MODEL
  DOCKERHUB_TOKEN
  DOCKERHUB_USERNAME
  ENVIRONMENT
  GOOGLE_API_KEY
  IP_SERVEUR
  MAX_SOURCES
  MAX_TOKENS
  SSH_SERVEUR
  TEMPERATURE
  VECTOR_STORE_TYPE
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "❌ Erreur : la variable d'environnement '$var' est manquante."
    exit 1
  fi
done

# === ✅ Génération du fichier ===

cat <<EOL > .env.prod
# ==== RAG Configuration ====
DEFAULT_MODEL=$DEFAULT_MODEL
TEMPERATURE=$TEMPERATURE
MAX_TOKENS=$MAX_TOKENS
MAX_SOURCES=$MAX_SOURCES

# ==== Google API ====
GOOGLE_API_KEY=$GOOGLE_API_KEY

# ==== Vector Store ====
VECTOR_STORE_TYPE=$VECTOR_STORE_TYPE

# ==== Application ====
ENVIRONMENT=$ENVIRONMENT
PORT=8000

# ==== Docker Hub (pour référence) ====
DOCKERHUB_USERNAME=$DOCKERHUB_USERNAME

# ==== Serveur (pour référence) ====
IP_SERVEUR=$IP_SERVEUR

# ==== Vector Store Type ====

VECTOR_STORE_TYPE=$VECTOR_STORE_TYPE

EOL

echo "✅ Fichier .env.prod créé avec succès."