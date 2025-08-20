#!/bin/bash
set -e

# ===================== 🔧 VARIABLES =====================

DOCKER_USERNAME="${DOCKERHUB_USERNAME:?}"
DOCKER_TOKEN="${DOCKERHUB_TOKEN:?}"

# Vérification des variables d'environnement
DEPLOY_REPO="git@github.com:AInelo/startax-deploy.git"
DEPLOY_DIR="startax-deploy"
IMAGE_NAME="rag-cgi-api"
TAG="latest"
FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
PROD_COMPOSE_FILE="rag-cgi-startax-docker-compose.prod.yml"

# Réseau Docker
NETWORK_NAME="startax-network"

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

# ===================== 🛑 ARRÊT DES SERVICES =====================

echo "🛑 Arrêt des services existants..."
docker compose -f "$PROD_COMPOSE_FILE" down

# ===================== 🧹 NETTOYAGE DES ANCIENNES IMAGES =====================

echo "🧹 Nettoyage des anciennes images $IMAGE_NAME..."

# Supprimer toutes les images de ce service (tagged et untagged)
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | grep "$DOCKER_USERNAME/$IMAGE_NAME" || true
echo "🗑️ Suppression de toutes les images $DOCKER_USERNAME/$IMAGE_NAME..."
docker images -q "$DOCKER_USERNAME/$IMAGE_NAME" | xargs -r docker rmi -f || true

# Nettoyage supplémentaire des images <none> liées
echo "🗑️ Nettoyage des images orphelines..."
docker image prune -f

# ===================== 🔐 DOCKER HUB =====================

echo "🔐 Connexion à Docker Hub..."
echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin

echo "📥 Pull de la dernière image : $FULL_IMAGE"
docker pull "$FULL_IMAGE"

# ===================== ✅ VÉRIFICATION =====================

echo "🔍 Vérification de l'image pullée..."
docker images | grep "$IMAGE_NAME"

# ===================== 🚀 DÉPLOIEMENT =====================

echo "🚀 Déploiement avec la nouvelle image..."
docker compose -f "$PROD_COMPOSE_FILE" up -d --force-recreate

# ===================== 🔍 VÉRIFICATION FINALE =====================

echo "🔍 Vérification du déploiement..."
sleep 5
docker ps | grep "$IMAGE_NAME"

echo "📋 Vérification du contenu du conteneur..."
CONTAINER_NAME=$(docker ps --format "{{.Names}}" | grep rag-cgi-api | head -1)
if [ ! -z "$CONTAINER_NAME" ]; then
  echo "🔍 Conteneur trouvé: $CONTAINER_NAME"
  docker exec "$CONTAINER_NAME" ls -la /app/data/cgi_documents/ || echo "❌ Impossible de vérifier le contenu"
else
  echo "❌ Aucun conteneur rag-cgi-api trouvé"
fi

# ===================== 🧹 NETTOYAGE FINAL =====================

rm -f .env.prod

echo "✅ Déploiement terminé avec succès."
echo "📊 Images actuelles:"
docker images | grep "$IMAGE_NAME"






























# #!/bin/bash
# set -e

# # ===================== 🔧 VARIABLES =====================

# DOCKER_USERNAME="${DOCKERHUB_USERNAME:?}"
# DOCKER_TOKEN="${DOCKERHUB_TOKEN:?}"

# # Vérification des variables d'environnement
# DEPLOY_REPO="git@github.com:AInelo/startax-deploy.git"
# DEPLOY_DIR="startax-deploy"
# IMAGE_NAME="rag-cgi-api"
# TAG="latest"
# FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
# PROD_COMPOSE_FILE="rag-cgi-startax-docker-compose.prod.yml"

# # Réseau Docker
# NETWORK_NAME="startax-network"

# # ===================== 🌐 RÉSEAU DOCKER =====================

# if ! docker network ls | grep -q "$NETWORK_NAME"; then
#   echo "🌐 Création du réseau Docker externe '$NETWORK_NAME'..."
#   docker network create "$NETWORK_NAME"
# else
#   echo "🌐 Réseau '$NETWORK_NAME' déjà existant."
# fi

# # ===================== 📦 CLONAGE / MAJ DEPÔT =====================

# if [ ! -d "$DEPLOY_DIR" ]; then
#   echo "📦 Clonage du dépôt de déploiement..."
#   git clone "$DEPLOY_REPO"
# else
#   echo "🔄 Le dépôt $DEPLOY_DIR existe déjà. Mise à jour..."
#   cd "$DEPLOY_DIR"
#   git pull origin main || git pull
#   cd ..
# fi

# cd "$DEPLOY_DIR"

# # ===================== 🔐 DOCKER HUB =====================

# echo "🔐 Connexion à Docker Hub..."
# echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin

# echo "📥 Pull de l'image : $FULL_IMAGE"
# docker pull "$FULL_IMAGE"

# # ===================== 🚀 DÉPLOIEMENT =====================

# echo "🚀 Lancement du service avec docker-compose..."
# docker compose -f "$PROD_COMPOSE_FILE" up -d

# rm -f .env.prod

# echo "✅ Déploiement terminé avec succès."