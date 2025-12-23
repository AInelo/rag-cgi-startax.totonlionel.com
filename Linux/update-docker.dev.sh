#!/bin/bash

# Script de mise à jour des services Docker
# Usage: ./update-docker.dev.sh [service_name]

# Charger les utilitaires Docker avec auto-détection
source "$(dirname "$0")/docker-utils.sh"

# Afficher la configuration détectée
show_detected_config

SERVICE_NAME=${1:-"$MAIN_SERVICE"}

cd ..

echo "🛠️ Build du service $SERVICE_NAME..."
docker compose -f "$COMPOSE_FILE" up -d --build

echo "📦 Recréation du conteneur (sans dépendances)..."
docker compose -f $COMPOSE_FILE up -d --no-deps $SERVICE_NAME

echo "✅ Mise à jour terminée."



# docker compose -f $COMPOSE_FILE build $SERVICE_NAME
