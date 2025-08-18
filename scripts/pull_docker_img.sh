#!/bin/bash
set -e

# ===================== 🔧 VARIABLES =====================

DOCKER_USERNAME="${DOCKERHUB_USERNAME:?}"
DOCKER_TOKEN="${DOCKERHUB_TOKEN:?}"


# Vérification des variables d'environnement
DEPLOY_REPO="git@github.com:urmapha-uac/urmapha-deploy.git"
DEPLOY_DIR="urmapha-deploy"
IMAGE_NAME="backend-pci-app"
TAG="latest"
FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
PROD_COMPOSE_FILE="rag-cgi-startax-docker-compose.prod.yml"

# Réseau Docker
NETWORK_NAME="urmapha-network"

# ===================== 🌐 RÉSEAU DOCKER =====================

if ! docker network ls | grep -q "$NETWORK_NAME"; then
  echo "🌐 Création du réseau Docker externe '$NETWORK_NAME'..."
  docker network create "$NETWORK_NAME"
else
  echo "🌐 Réseau '$NETWORK_NAME' déjà existant."
fi

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

echo "📥 Pull de l'image : $FULL_IMAGE"
docker pull "$FULL_IMAGE"

# ===================== 🚀 DÉPLOIEMENT =====================

echo "🚀 Lancement du service avec docker-compose..."
docker compose -f "$PROD_COMPOSE_FILE" up -d

rm -f .env.prod

echo "✅ Déploiement terminé avec succès."