#!/bin/bash

# Script de démarrage pour le service RAG CGI avec Google Gemini
# Auteur: Assistant IA
# Date: $(date)

echo "🚀 Démarrage du service RAG CGI avec Google Gemini"
echo "=================================================="

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier si Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier si la clé API Google est configurée
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  Variable GOOGLE_API_KEY non définie."
    echo "📝 Veuillez configurer votre clé API Google AI Studio:"
    echo "   1. Allez sur https://aistudio.google.com/app/apikey"
    echo "   2. Créez une clé API gratuite"
    echo "   3. Exportez la variable: export GOOGLE_API_KEY='votre_clé'"
    echo ""
    echo "🔑 Ou créez un fichier .env avec: GOOGLE_API_KEY=votre_clé"
    echo ""
    
    # Demander la clé API
    read -p "Entrez votre clé API Google AI Studio: " api_key
    if [ -n "$api_key" ]; then
        export GOOGLE_API_KEY="$api_key"
        echo "✅ Clé API configurée pour cette session"
    else
        echo "❌ Clé API requise pour continuer"
        exit 1
    fi
fi

# Vérifier si le fichier .env existe
if [ ! -f ".env" ]; then
    echo "📝 Création du fichier .env..."
    cp config.env.example .env
    echo "✅ Fichier .env créé. Veuillez y ajouter votre clé API Google."
    echo "🔑 Remplacez 'your_google_api_key_here' par votre vraie clé API"
    exit 1
fi

# Vérifier si la clé API est dans le fichier .env
if grep -q "your_google_api_key_here" .env; then
    echo "⚠️  Clé API non configurée dans .env"
    echo "🔑 Veuillez remplacer 'your_google_api_key_here' par votre vraie clé API"
    exit 1
fi

echo "✅ Configuration vérifiée"
echo "🔑 Clé API Google: ${GOOGLE_API_KEY:0:10}..."

# Créer les répertoires nécessaires
echo "📁 Création des répertoires..."
mkdir -p data vector_db static

# Vérifier s'il y a des documents CGI
if [ ! "$(ls -A data 2>/dev/null)" ]; then
    echo "⚠️  Répertoire 'data' vide. Ajoutez vos documents CGI (.md) avant de continuer."
    echo "📚 Exemple de structure:"
    echo "   data/"
    echo "   ├── cgi_documents/"
    echo "   │   ├── titre_1.md"
    echo "   │   ├── titre_2.md"
    echo "   │   └── ..."
    echo ""
    read -p "Voulez-vous continuer sans documents ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Construire et démarrer le service
echo "🔨 Construction de l'image Docker..."
docker-compose -f docker-compose.simple.yml build

if [ $? -eq 0 ]; then
    echo "✅ Image construite avec succès"
    
    echo "🚀 Démarrage du service..."
    docker-compose -f docker-compose.simple.yml up -d
    
    if [ $? -eq 0 ]; then
        echo "✅ Service démarré avec succès!"
        echo ""
        echo "🌐 Interface web disponible sur: http://localhost:8080"
        echo "📊 Health check: http://localhost:8080/health"
        echo "📈 Statistiques: http://localhost:8080/stats"
        echo ""
        echo "📋 Commandes utiles:"
        echo "   - Voir les logs: docker-compose -f docker-compose.simple.yml logs -f"
        echo "   - Arrêter: docker-compose -f docker-compose.simple.yml down"
        echo "   - Redémarrer: docker-compose -f docker-compose.simple.yml restart"
        echo ""
        echo "🔍 Vérification du statut..."
        sleep 5
        curl -s http://localhost:8080/health | python3 -m json.tool 2>/dev/null || echo "Service en cours de démarrage..."
        
    else
        echo "❌ Erreur lors du démarrage du service"
        exit 1
    fi
else
    echo "❌ Erreur lors de la construction de l'image"
    exit 1
fi 