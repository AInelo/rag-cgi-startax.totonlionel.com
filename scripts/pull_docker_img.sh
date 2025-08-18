#!/bin/bash
set -e

# ===================== 🔧 VARIABLES =====================

DOCKER_USERNAME="${DOCKERHUB_USERNAME:?}"
DOCKER_TOKEN="${DOCKERHUB_TOKEN:?}"

DEPLOY_REPO="git@github.com:urmapha-uac/urmapha-deploy.git"
DEPLOY_DIR="urmapha-deploy"
IMAGE_NAME="backend-pci-app"
TAG="latest"
FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
PROD_COMPOSE_FILE="backend-pci-app-docker-compose.prod.yml"

# Réseau Docker
NETWORK_NAME="urmapha-network"

# Volumes
URMAPHA_DATABASE_DIR="/home/admin/URMAPHA_DATABASE"
MYSQL_VOLUME_DIR="$URMAPHA_DATABASE_DIR/mysql"
MONGO_VOLUME_DIR="$URMAPHA_DATABASE_DIR/mongo"

# ===================== 🌐 RÉSEAU DOCKER =====================

if ! docker network ls | grep -q "$NETWORK_NAME"; then
  echo "🌐 Création du réseau Docker externe '$NETWORK_NAME'..."
  docker network create "$NETWORK_NAME"
else
  echo "🌐 Réseau '$NETWORK_NAME' déjà existant."
fi

# ===================== 📁 VOLUMES LOCAUX =====================
echo "📁 Vérification et création des dossiers de volumes..."

mkdir -p "$MYSQL_VOLUME_DIR"
mkdir -p "$MONGO_VOLUME_DIR"

if [ "$(id -u)" -eq 0 ]; then
  echo "🔧 Root détecté : modification des permissions..."

  # chmod seulement sur les dossiers, pas sur les fichiers internes (optionnel)
  find "$URMAPHA_DATABASE_DIR" -type d -exec chmod 755 {} \;

  chown -R 999:999 "$MYSQL_VOLUME_DIR"
  chown -R 999:999 "$MONGO_VOLUME_DIR"
else
  echo "ℹ️ Pas root : on saute chmod/chown pour éviter erreurs."
fi

echo "✅ Dossiers de volume prêts :"
echo "   - MySQL : $MYSQL_VOLUME_DIR"
echo "   - Mongo : $MONGO_VOLUME_DIR"









# echo "📁 Vérification et création des dossiers de volumes..."

# mkdir -p "$MYSQL_VOLUME_DIR"
# mkdir -p "$MONGO_VOLUME_DIR"

# # Donne les permissions nécessaires (ajuste le user si besoin)
# chmod -R 755 "$URMAPHA_DATABASE_DIR"

# if [ "$(id -u)" -eq 0 ]; then
#   chown -R 999:999 "$MYSQL_VOLUME_DIR"
#   chown -R 999:999 "$MONGO_VOLUME_DIR"
# else
#   echo "ℹ️ Pas root : on saute les chown."
# fi

# echo "✅ Dossiers de volume prêts :"
# echo "   - MySQL : $MYSQL_VOLUME_DIR"
# echo "   - Mongo : $MONGO_VOLUME_DIR"

# ===================== 📦 CLONAGE / MAJ DEPÔT =====================

if [ ! -d "$DEPLOY_DIR" ]; then
  echo "📦 Clonage du dépôt de déploiement..."
  git clone "$DEPLOY_REPO"
else
  echo "🔄 Le dépôt $DEPLOY_DIR existe déjà. Mise à jour..."
  cd "$DEPLOY_DIR"
  git pull origin main || git pull
  cd ..
fi

cd "$DEPLOY_DIR"

# ===================== 🔐 DOCKER HUB =====================

echo "🔐 Connexion à Docker Hub..."
echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin

echo "📥 Pull de l’image : $FULL_IMAGE"
docker pull "$FULL_IMAGE"

# ===================== 🚀 DÉPLOIEMENT =====================

echo "🚀 Lancement du service avec docker-compose..."
docker compose -f "$PROD_COMPOSE_FILE" up -d


rm -f .env.prod

echo "✅ Déploiement terminé avec succès."

















# chown -R 999:999 "$MYSQL_VOLUME_DIR"  # 999 est l'UID par défaut de MySQL dans le conteneur
# chown -R 999:999 "$MONGO_VOLUME_DIR"  # 999 est l'UID de MongoDB aussi