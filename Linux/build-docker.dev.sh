#!/bin/bash

# Script de build des images Docker
# Usage: ./build-docker.dev.sh [service_name]

# Charger les utilitaires Docker avec auto-détection
source "$(dirname "$0")/docker-utils.sh"

# Afficher la configuration détectée
show_detected_config

SERVICE_NAME=${1:-"$MAIN_SERVICE"}

cd ..

echo "🔨 Build de l'image Docker pour le service: $SERVICE_NAME"

# Vérifier si le service existe dans le compose
if ! docker compose -f "$COMPOSE_FILE" config --services | grep -q "^$SERVICE_NAME$"; then
    echo "❌ Service '$SERVICE_NAME' non trouvé dans $COMPOSE_FILE"
    echo "📋 Services disponibles:"
    docker compose -f "$COMPOSE_FILE" config --services
    exit 1
fi

echo "🛠️ Construction de l'image..."
docker compose -f "$COMPOSE_FILE" build "$SERVICE_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Build réussi pour le service: $SERVICE_NAME"
    
    # Afficher les informations sur l'image créée
    echo "📊 Informations sur l'image:"
    docker images | grep "$(basename $(pwd))" | head -5
    
    echo ""
    echo "💡 Pour démarrer le service: ./start-docker.dev.sh"
    echo "💡 Pour mettre à jour: ./update-docker.dev.sh"
else
    echo "❌ Erreur lors du build du service: $SERVICE_NAME"
    exit 1
fi
