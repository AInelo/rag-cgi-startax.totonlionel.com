#!/bin/bash

# Charger les utilitaires Docker avec auto-détection
source "$(dirname "$0")/docker-utils.sh"

# Afficher la configuration détectée
show_detected_config

# Vérifie si le réseau Docker existe
if ! docker network ls --format '{{.Name}}' | grep -wq "$NETWORK_NAME"; then
  echo "🔧 Réseau '$NETWORK_NAME' non trouvé. Création..."
  docker network create "$NETWORK_NAME"
else
  echo "✅ Réseau '$NETWORK_NAME' déjà existant."
fi

cd ..

# Vérifier si l'image du service principal existe
echo "🔍 Vérification de l'image du service principal: $MAIN_SERVICE"
# Extraire le nom de l'image depuis le compose file
IMAGE_NAME=$(docker compose -f "$COMPOSE_FILE" config | grep -A 5 "services:" | grep -A 5 "$MAIN_SERVICE:" | grep "image:" | head -1 | sed 's/.*image: *//' | tr -d '"' | tr -d "'" || echo "")

# Si pas d'image spécifiée, utiliser le nom du projet
if [ -z "$IMAGE_NAME" ]; then
    IMAGE_NAME="$(basename $(pwd)):dev"
fi

if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}$"; then
    echo "⚠️ Image '$IMAGE_NAME' non trouvée. Build automatique en cours..."
    echo "🔨 Build de l'image..."
    docker compose -f "$COMPOSE_FILE" build "$MAIN_SERVICE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Build réussi!"
    else
        echo "❌ Erreur lors du build. Arrêt du processus."
        exit 1
    fi
else
    echo "✅ Image '$IMAGE_NAME' déjà existante."
fi

# Lancement du docker compose
echo "🚀 Lancement du docker compose ($COMPOSE_FILE)..."
docker compose -f "$COMPOSE_FILE" up -d
