# 🐳 Docker Compose - RAG CGI API

Ce projet utilise Docker Compose pour gérer différents environnements : développement, build et production.

## 📁 Structure des fichiers

- `docker-compose.dev.yml` - Environnement de développement
- `docker-compose.build.yml` - Environnement de build pour GitHub Actions
- `docker-compose.prod.yml` - Environnement de production
- `Dockerfile.dev` - Image Docker pour le développement
- `Dockerfile` - Image Docker pour la production

## 🚀 Développement

### Démarrage rapide

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer les variables d'environnement
nano .env

# Démarrer l'environnement de développement
docker-compose -f docker-compose.dev.yml up -d

# Voir les logs
docker-compose -f docker-compose.dev.yml logs -f rag-cgi-api

# Arrêter l'environnement
docker-compose -f docker-compose.dev.yml down
```

### Services inclus

- **rag-cgi-api** : API FastAPI avec hot-reload (port 8000)
- **chromadb** : Base de données vectorielle (port 8001)
- **redis** : Cache et sessions (port 6379)
- **nginx** : Reverse proxy et interface statique (port 80)

### Fonctionnalités de développement

- ✅ Hot-reload automatique du code
- ✅ Volumes montés pour le code source
- ✅ Outils de développement (pytest, black, flake8)
- ✅ Debug et logs détaillés
- ✅ Interface de test accessible sur http://localhost

## 🔨 Build GitHub Actions

### Utilisation

```bash
# Build de l'image pour les tests
docker-compose -f docker-compose.build.yml up -d

# Exécuter les tests
docker-compose -f docker-compose.build.yml exec rag-cgi-builder python -m pytest

# Arrêter l'environnement de build
docker-compose -f docker-compose.build.yml down
```

### Services inclus

- **rag-cgi-builder** : Service de build avec tests
- **chromadb** : Base de données pour les tests
- **redis** : Cache pour les tests

### Intégration CI/CD

```yaml
# .github/workflows/build.yml
- name: Build and test
  run: |
    docker-compose -f docker-compose.build.yml up -d
    docker-compose -f docker-compose.build.yml exec -T rag-cgi-builder python -m pytest
    docker-compose -f docker-compose.build.yml down
```

## 🚀 Production

### Démarrage

```bash
# Définir les variables d'environnement
export DOCKER_REGISTRY="your-registry.com"
export IMAGE_TAG="v1.0.0"
export OPENAI_API_KEY="your-key"
export REDIS_PASSWORD="secure-password"

# Démarrer l'environnement de production
docker-compose -f docker-compose.prod.yml up -d

# Vérifier le statut
docker-compose -f docker-compose.prod.yml ps
```

### Services inclus

- **rag-cgi-api** : API en production avec health checks
- **chromadb** : Base de données vectorielle sécurisée
- **redis** : Cache avec authentification
- **nginx** : Reverse proxy avec SSL et sécurité
- **prometheus** : Monitoring et métriques

### Configuration SSL

```bash
# Créer le dossier SSL
mkdir -p ssl

# Générer un certificat auto-signé (pour les tests)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# Ou utiliser Let's Encrypt
certbot certonly --standalone -d yourdomain.com
```

## 🔧 Variables d'environnement

### Développement (.env)

```bash
ENVIRONMENT=development
OPENAI_API_KEY=your_key
REDIS_URL=redis://redis:6379
CHROMA_DB_IMPL=duckdb+parquet
PERSIST_DIRECTORY=/app/vector_db
```

### Production

```bash
ENVIRONMENT=production
DOCKER_REGISTRY=your-registry.com
IMAGE_TAG=v1.0.0
OPENAI_API_KEY=your_key
REDIS_PASSWORD=secure_password
```

## 📊 Monitoring

### Prometheus

- Métriques de l'API : http://localhost:9090
- Endpoint métriques : `/metrics`
- Configuration : `prometheus.yml`

### Health Checks

- API : `GET /health`
- Nginx : `GET /health`
- ChromaDB : `GET /api/v1/heartbeat`

## 🛠️ Commandes utiles

### Développement

```bash
# Rebuild l'image de développement
docker-compose -f docker-compose.dev.yml build --no-cache

# Redémarrer un service
docker-compose -f docker-compose.dev.yml restart rag-cgi-api

# Voir les logs d'un service
docker-compose -f docker-compose.dev.yml logs -f chromadb
```

### Production

```bash
# Mettre à jour l'image
docker-compose -f docker-compose.prod.yml pull

# Redémarrer avec la nouvelle image
docker-compose -f docker-compose.prod.yml up -d

# Sauvegarder les volumes
docker run --rm -v rag-cgi-prod_redis_prod_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .
```

## 🔒 Sécurité

### Développement
- Ports exposés localement uniquement
- Pas d'authentification Redis
- Logs détaillés pour le debug

### Production
- SSL/TLS obligatoire
- Authentification Redis
- Rate limiting Nginx
- Headers de sécurité
- Health checks
- Monitoring Prometheus

## 📝 Troubleshooting

### Problèmes courants

1. **Port déjà utilisé**
   ```bash
   # Vérifier les ports utilisés
   netstat -tulpn | grep :8000
   
   # Changer le port dans docker-compose
   ports:
     - "8001:8000"
   ```

2. **Permissions de volumes**
   ```bash
   # Corriger les permissions
   sudo chown -R $USER:$USER ./data ./vector_db
   ```

3. **Mémoire insuffisante**
   ```bash
   # Augmenter la mémoire Docker
   # Dans Docker Desktop > Settings > Resources
   ```

4. **ChromaDB ne démarre pas**
   ```bash
   # Vérifier les logs
   docker-compose logs chromadb
   
   # Redémarrer le service
   docker-compose restart chromadb
   ```

## 🚀 Prochaines étapes

- [ ] Ajouter Grafana pour la visualisation
- [ ] Configurer l'alerting Prometheus
- [ ] Ajouter des tests d'intégration
- [ ] Configurer le backup automatique
- [ ] Ajouter l'auto-scaling 