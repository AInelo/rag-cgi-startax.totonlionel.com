#!/bin/bash
set -euo pipefail

echo "📦 Génération du fichier .env.prod à partir des variables d’environnement..."

# === ✅ Vérification explicite de chaque variable ===

required_vars=(
  DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME
  MONGO_URL MONGO_DB_NAME
  EMAIL_HOST EMAIL_USER EMAIL_PASS
  JWT_SECRET FRONTEND_URL
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "❌ Erreur : la variable d'environnement '$var' est manquante."
    exit 1
  fi
done

# === ✅ Génération du fichier ===

cat <<EOL > .env.prod
# ==== MySQL ====
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

# ==== MongoDB ====
MONGO_URL=$MONGO_URL
MONGO_DB_NAME=$MONGO_DB_NAME

# ==== Email ====
EMAIL_HOST=$EMAIL_HOST
EMAIL_USER=$EMAIL_USER
EMAIL_PASS=$EMAIL_PASS
EMAIL_PORT=465
EMAIL_SECURE=true

# ==== Auth ====
JWT_SECRET=$JWT_SECRET
JWT_EXPIRES_IN=7d

# ==== Frontend ====
FRONTEND_URL=$FRONTEND_URL

# ==== App ====
PORT=5002
EOL

echo "✅ Fichier .env.prod créé avec succès."