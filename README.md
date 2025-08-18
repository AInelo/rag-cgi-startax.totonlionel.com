# 🏛️ RAG CGI - Assistant IA pour le Code Général des Impôts du Bénin

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)
[![Google AI](https://img.shields.io/badge/Google%20AI-Gemini-orange.svg)](https://aistudio.google.com)

Un système de **Recherche Augmentée par Génération (RAG)** intelligent pour interroger le Code Général des Impôts du Bénin en langage naturel, alimenté par Google Gemini AI.

## 🚀 Fonctionnalités

- **🔍 Recherche intelligente** dans 2714+ documents CGI indexés
- **🤖 IA conversationnelle** avec Google Gemini 2.0 Flash
- **📚 Contexte adaptatif** (fiscal, entreprise, particulier, général)
- **⚡ Streaming temps réel** avec Server-Sent Events (SSE)
- **🗄️ Base vectorielle** ultra-légère avec scikit-learn
- **🌐 Interface web** intuitive pour les tests
- **📊 Monitoring** et logs détaillés

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Interface     │    │   FastAPI        │    │   Google AI     │
│   Web/API      │◄──►│   RAG Service    │◄──►│   Gemini API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Vector Store   │
                       │   (scikit-learn) │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Documents      │
                       │   CGI Markdown   │
                       └──────────────────┘
```

## 📋 Prérequis

- **Docker** et **Docker Compose** installés
- **Clé API Google AI Studio** (gratuite)
- **Git** pour cloner le projet

## 🛠️ Installation

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd rag-cgi-startax.totonlionel.com
```

### 2. Configurer l'environnement

Créez un fichier `.env` à la racine du projet :

```bash
# Configuration pour le service RAG CGI avec Google Gemini
# Obtenez votre clé API gratuite sur: https://aistudio.google.com/app/apikey

# Clé API Google AI Studio (requise pour Gemini)
GOOGLE_API_KEY=AIzaSyA_Z-VotreCléAPI

# Configuration de l'environnement
ENVIRONMENT=development

# Configuration du service
VECTOR_STORE_TYPE=sklearn
MAX_SOURCES=5
TEMPERATURE=0.3
MAX_TOKENS=2048

# Configuration des modèles Gemini gratuits
DEFAULT_MODEL=gemini-2.0-flash
# Modèles disponibles gratuitement:
# - gemini-2.0-flash
# - gemini-1.5-flash
# - gemini-1.1.5-flash-8b
# - gemini-1.5-pro
# - gemma-3
# - gemma-3n

# Configuration du serveur
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### 3. Obtenir une clé API Google AI Studio

1. Allez sur [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Créez un compte gratuit si nécessaire
3. Générez une nouvelle clé API
4. Copiez la clé dans votre fichier `.env`

## 🚀 Démarrage rapide

### Démarrage en développement

```bash
# Démarrer le service avec reconstruction automatique
docker-compose -f docker-compose.simple.yml up -d --build

# Vérifier le statut
docker-compose -f docker-compose.simple.yml ps

# Voir les logs
docker-compose -f docker-compose.simple.yml logs -f
```

### Démarrage en production

```bash
# Démarrer sans reconstruction
docker-compose -f docker-compose.simple.yml up -d

# Vérifier le statut
docker ps
```

## 🌐 Utilisation

### Interface web

Ouvrez votre navigateur sur : **http://localhost:8080**

### API REST

```bash
# Health check
curl http://localhost:8080/health

# Test de recherche
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels sont les taux de TVA au Bénin ?",
    "context_type": "fiscal",
    "max_sources": 3
  }'
```

### Streaming SSE

```bash
# Test du streaming
curl -N http://localhost:8080/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comment calculer l\'impôt sur les sociétés ?",
    "context_type": "entreprise",
    "max_sources": 5
  }'
```

## 🧪 Tests et développement

### Scripts de test inclus

```bash
# Test de diagnostic complet
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 python3 /app/diagnostic_rag.py

# Test de la correction du filtrage
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 python3 /app/test_correction.py

# Test de recherche simple
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 python3 /app/test_simple.py
```

### Créer vos propres tests

```bash
# Copier un script de test dans le container
docker cp mon_test.py rag-cgi-startaxtotonlionelcom-rag-cgi-api-1:/app/

# Exécuter le test
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 python3 /app/mon_test.py
```

## 🔧 Configuration avancée

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Clé API Google AI Studio | Requise |
| `ENVIRONMENT` | Environnement (dev/prod) | `development` |
| `VECTOR_STORE_TYPE` | Type de base vectorielle | `sklearn` |
| `MAX_SOURCES` | Nombre max de sources | `5` |
| `TEMPERATURE` | Température de génération | `0.3` |
| `MAX_TOKENS` | Tokens max de réponse | `2048` |
| `DEFAULT_MODEL` | Modèle Gemini par défaut | `gemini-2.0-flash` |

### Modèles Gemini disponibles

- **`gemini-2.0-flash`** : Modèle gratuit le plus récent
- **`gemini-1.5-flash`** : Modèle rapide et efficace
- **`gemini-1.5-pro`** : Modèle avancé pour tâches complexes
- **`gemma-3`** : Modèle léger et rapide

## 📁 Structure du projet

```
rag-cgi-startax.totonlionel.com/
├── 📁 app/                          # Code source principal
│   ├── 📁 services/                 # Services métier
│   │   ├── rag_service.py          # Service RAG principal
│   │   ├── llm_service_gemini.py   # Service Google Gemini
│   │   └── embedding_service.py    # Service d'embeddings
│   ├── 📁 database/                 # Base de données
│   │   └── vector_store.py         # Store vectoriel scikit-learn
│   ├── 📁 models/                   # Modèles de données
│   ├── 📁 utils/                    # Utilitaires
│   └── main.py                      # Point d'entrée FastAPI
├── 📁 data/                         # Documents source
│   └── 📁 cgi_documents/           # Documents CGI Markdown
├── 📁 vector_db/                    # Base vectorielle persistée
├── 📁 static/                       # Fichiers statiques
├── 📄 docker-compose.simple.yml     # Configuration Docker
├── 📄 Dockerfile.simple             # Image Docker
├── 📄 requirements.simple.txt       # Dépendances Python
├── 📄 .env                          # Variables d'environnement
└── 📄 README.md                     # Ce fichier
```

## 🐛 Dépannage

### Problèmes courants

#### 1. Container ne démarre pas

```bash
# Vérifier les logs
docker-compose -f docker-compose.simple.yml logs

# Vérifier la configuration
docker-compose -f docker-compose.simple.yml config
```

#### 2. Erreur de clé API

```bash
# Vérifier la variable d'environnement
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 env | grep GOOGLE

# Redémarrer avec la nouvelle clé
docker-compose -f docker-compose.simple.yml down
docker-compose -f docker-compose.simple.yml up -d --build
```

#### 3. Aucune source trouvée

```bash
# Vérifier l'indexation
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 python3 /app/diagnostic_rag.py

# Vérifier les documents
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 ls -la /app/data/cgi_documents
```

### Commandes utiles

```bash
# Redémarrer le service
docker-compose -f docker-compose.simple.yml restart

# Reconstruire l'image
docker-compose -f docker-compose.simple.yml up -d --build

# Nettoyer les volumes
docker-compose -f docker-compose.simple.yml down -v

# Accéder au container
docker exec -it rag-cgi-startaxtotonlionelcom-rag-cgi-api-1 bash
```

## 📊 Monitoring et logs

### Logs en temps réel

```bash
# Suivre les logs du service
docker-compose -f docker-compose.simple.yml logs -f rag-cgi-api

# Logs du container
docker logs -f rag-cgi-startaxtotonlionelcom-rag-cgi-api-1
```

### Métriques de santé

```bash
# Health check
curl http://localhost:8080/health

# Statistiques du service
curl http://localhost:8080/stats
```

## 🔒 Sécurité

- **Clé API** : Stockée dans le fichier `.env` (ne pas commiter)
- **Ports** : Exposés uniquement sur localhost par défaut
- **Utilisateur** : Container exécuté avec un utilisateur non-root
- **Volumes** : Données persistées dans des volumes Docker sécurisés

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Google AI Studio** pour l'accès gratuit à Gemini
- **FastAPI** pour le framework web moderne
- **scikit-learn** pour la base vectorielle légère
- **Docker** pour la containerisation

## 📞 Support

Pour toute question ou problème :

- 📧 Créez une issue sur GitHub
- 🐛 Utilisez les scripts de diagnostic inclus
- 📚 Consultez la documentation des composants

---

**Développé avec ❤️ pour simplifier l'accès au Code Général des Impôts du Bénin** 