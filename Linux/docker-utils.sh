#!/bin/bash

# Utilitaires Docker pour les scripts Linux/
# Ce fichier peut être sourcé par d'autres scripts
# Adapté pour le projet RAG CGI

# Fonction pour auto-détecter le fichier compose
detect_compose_file() {
    local compose_file=""
    
    # Priorité 1: docker-compose.simple.yml (fichier principal du projet RAG CGI)
    if [ -f "../docker-compose.simple.yml" ]; then
        compose_file="docker-compose.simple.yml"
    # Priorité 2: chercher n'importe quel fichier *-docker-compose.dev.yml
    elif [ -f "../rag-cgi-startax-docker-compose.dev.yml" ]; then
        compose_file="rag-cgi-startax-docker-compose.dev.yml"
    else
        # Fallback: chercher n'importe quel fichier *docker-compose*.yml
        compose_file=$(find .. -maxdepth 1 -name "*docker-compose*.yml" | head -1 | xargs basename)
    fi
    
    if [ -z "$compose_file" ]; then
        echo "❌ Aucun fichier docker-compose*.yml trouvé dans le répertoire parent"
        exit 1
    fi
    
    echo "$compose_file"
}

# Fonction pour auto-détecter le nom du réseau
detect_network_name() {
    local compose_file="$1"
    local network_name=""
    
    # Extraire le nom du réseau depuis le fichier compose
    if [ -f "../$compose_file" ]; then
        # Chercher le nom du réseau dans la section networks (priorité: name: dans un réseau externe)
        network_name=$(grep -A 5 "networks:" "../$compose_file" | grep -A 3 "external:" | grep -E "^\s*name:" | head -1 | sed 's/.*name: *//' | tr -d '"' | tr -d "'" | xargs)
        
        # Si pas trouvé, chercher le nom d'un réseau marqué comme externe
        if [ -z "$network_name" ]; then
            # Chercher un réseau avec external: true et extraire son nom
            network_name=$(grep -B 2 "external: true" "../$compose_file" | grep -E "^\s*[a-zA-Z0-9_-]+:" | head -1 | sed 's/://g' | xargs)
        fi
        
        # Si toujours pas trouvé, chercher simplement le nom dans la section networks
        if [ -z "$network_name" ]; then
            network_name=$(grep -A 10 "networks:" "../$compose_file" | grep -E "^\s*name:" | head -1 | sed 's/.*name: *//' | tr -d '"' | tr -d "'" | xargs)
        fi
    fi
    
    # Fallback: utiliser startax_network (réseau de production partagé)
    if [ -z "$network_name" ]; then
        network_name="startax_network"
    fi
    
    echo "$network_name"
}

# Fonction pour auto-détecter le nom du service principal
detect_main_service() {
    local compose_file="$1"
    local service_name=""
    
    # Extraire le premier service du fichier compose (en ignorant version, services, volumes, networks)
    if [ -f "../$compose_file" ]; then
        service_name=$(grep -E "^\s*[a-zA-Z0-9_-]+:" "../$compose_file" | grep -v -E "^\s*(version|services|volumes|networks):" | head -1 | sed 's/://g' | xargs)
    fi
    
    # Fallback: utiliser le nom par défaut pour RAG CGI
    if [ -z "$service_name" ]; then
        service_name="rag-cgi-api"
    fi
    
    echo "$service_name"
}

# Variables globales auto-détectées
COMPOSE_FILE=$(detect_compose_file)
NETWORK_NAME=$(detect_network_name "$COMPOSE_FILE")
MAIN_SERVICE=$(detect_main_service "$COMPOSE_FILE")

# Fonction pour afficher les informations détectées
show_detected_config() {
    echo "🔍 Configuration auto-détectée:"
    echo "   📄 Fichier compose: $COMPOSE_FILE"
    echo "   🌐 Réseau: $NETWORK_NAME"
    echo "   🚀 Service principal: $MAIN_SERVICE"
    echo ""
}
