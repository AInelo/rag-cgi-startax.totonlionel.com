# 🐳 Scripts Docker - Guide d'utilisation RAG CGI

Ce dossier contient tous les scripts nécessaires pour gérer votre environnement Docker de développement de manière automatisée.

## 📦 Projet : RAG CGI - Assistant IA pour le Code Général des Impôts

Ces scripts sont configurés pour le projet **rag-cgi-startax.totonlionel.com** qui utilise :
- **Service principal** : `rag-cgi-api` (FastAPI/Python)
- **Base vectorielle** : Volume Docker pour les embeddings
- **Réseau** : `startax_network` (réseau partagé avec la production - auto-détecté)

## 📋 Configuration auto-détectée

Tous les scripts détectent automatiquement votre configuration :
- **Fichier compose** : `docker-compose.simple.yml`
- **Réseau** : `startax_network` (même réseau que la production)
- **Service principal** : `rag-cgi-api`

## 🚀 Ordre d'utilisation recommandé

### 1️⃣ **PREMIÈRE FOIS / NOUVEAU PROJET**

```bash
# Option 1 : Build complet + démarrage (recommandé)
./build-and-start.sh

# Option 2 : Build puis start séparément
./build-docker.dev.sh && ./start-docker.dev.sh
```

### 2️⃣ **DÉVELOPPEMENT QUOTIDIEN**

```bash
# Démarrage simple (build auto si nécessaire)
./start-docker.dev.sh

# Ou si vous voulez forcer le rebuild
./build-and-start.sh --force-rebuild
```

### 3️⃣ **MAINTENANCE**

```bash
# Redémarrage simple
./restart-docker.dev.sh

# Redémarrage avec rebuild
./restart-docker.dev.sh rag-cgi-api --rebuild

# Mise à jour du service
./update-docker.dev.sh
```

### 4️⃣ **DEBUGGING**

```bash
# Voir tous les logs
./logs-docker.dev.sh

# Suivre les logs en temps réel
./logs-docker.dev.sh rag-cgi-api -f

# Accéder au conteneur
./exec-docker.dev.sh rag-cgi-api bash
```

### 5️⃣ **SAUVEGARDE**

```bash
# Sauvegarder les volumes (base vectorielle)
./backup_volume.sh

# Restaurer une sauvegarde
./restore_volume.sh
```

### 6️⃣ **NETTOYAGE**

```bash
# Nettoyage léger
./clean-docker.dev.sh

# Nettoyage complet
./clean-docker.dev.sh --all

# Supprimer les volumes
./delete_volume-docker.sh
```

## 📝 Scripts disponibles

| Script | Description | Usage |
|--------|-------------|-------|
| `build-and-start.sh` | Build complet + démarrage (recommandé pour la première fois) | `./build-and-start.sh [service] [--force-rebuild]` |
| `start-docker.dev.sh` | Démarrage avec build auto si nécessaire | `./start-docker.dev.sh` |
| `build-docker.dev.sh` | Build uniquement | `./build-docker.dev.sh [service]` |
| `restart-docker.dev.sh` | Redémarrage des services | `./restart-docker.dev.sh [service] [--rebuild]` |
| `update-docker.dev.sh` | Mise à jour du service | `./update-docker.dev.sh [service]` |
| `logs-docker.dev.sh` | Affichage des logs | `./logs-docker.dev.sh [service] [options]` |
| `exec-docker.dev.sh` | Exécution de commandes dans le conteneur | `./exec-docker.dev.sh [service] [command]` |
| `backup_volume.sh` | Sauvegarde des volumes | `./backup_volume.sh [backup_name]` |
| `restore_volume.sh` | Restauration des volumes | `./restore_volume.sh [backup_name]` |
| `clean-docker.dev.sh` | Nettoyage des ressources Docker | `./clean-docker.dev.sh [--force] [--all]` |
| `delete_volume-docker.sh` | Suppression des volumes | `./delete_volume-docker.sh` |
| `test-auto-detection.sh` | Test de l'auto-détection | `./test-auto-detection.sh` |
| `help.sh` | Script d'aide | `./help.sh` |

## 🔧 Détails des scripts

### Build et Démarrage

#### `build-and-start.sh`
Script principal pour build + start en une commande.

```bash
# Build et start du service principal
./build-and-start.sh

# Build et start d'un service spécifique
./build-and-start.sh rag-cgi-api

# Force le rebuild même si l'image existe
./build-and-start.sh rag-cgi-api --force-rebuild
```

#### `start-docker.dev.sh`
Démarrage intelligent avec build automatique si nécessaire.

```bash
# Démarrage simple
./start-docker.dev.sh
```

#### `build-docker.dev.sh`
Build uniquement d'un service.

```bash
# Build du service principal
./build-docker.dev.sh

# Build d'un service spécifique
./build-docker.dev.sh rag-cgi-api
```

### Maintenance

#### `restart-docker.dev.sh`
Redémarrage des services avec options.

```bash
# Redémarrage de tous les services
./restart-docker.dev.sh

# Redémarrage d'un service spécifique
./restart-docker.dev.sh rag-cgi-api

# Redémarrage avec rebuild
./restart-docker.dev.sh rag-cgi-api --rebuild
```

#### `update-docker.dev.sh`
Mise à jour d'un service.

```bash
# Mise à jour du service principal
./update-docker.dev.sh

# Mise à jour d'un service spécifique
./update-docker.dev.sh rag-cgi-api
```

### Debugging

#### `logs-docker.dev.sh`
Affichage des logs avec options avancées.

```bash
# Logs de tous les services
./logs-docker.dev.sh

# Logs d'un service spécifique
./logs-docker.dev.sh rag-cgi-api

# Suivi des logs en temps réel
./logs-docker.dev.sh rag-cgi-api -f

# 100 dernières lignes
./logs-docker.dev.sh rag-cgi-api --tail=100

# Logs depuis un timestamp
./logs-docker.dev.sh rag-cgi-api --since=2024-01-01T10:00:00
```

#### `exec-docker.dev.sh`
Exécution de commandes dans le conteneur.

```bash
# Accéder au shell du service principal
./exec-docker.dev.sh

# Accéder au shell d'un service spécifique
./exec-docker.dev.sh rag-cgi-api bash

# Exécuter une commande Python
./exec-docker.dev.sh rag-cgi-api python3 -m pytest

# Lister les fichiers
./exec-docker.dev.sh rag-cgi-api ls -la
```

### Sauvegarde et Restauration

#### `backup_volume.sh`
Sauvegarde des volumes Docker (important pour la base vectorielle).

```bash
# Sauvegarde avec nom automatique
./backup_volume.sh

# Sauvegarde avec nom personnalisé
./backup_volume.sh ma_sauvegarde
```

#### `restore_volume.sh`
Restauration des volumes depuis une sauvegarde.

```bash
# Lister les sauvegardes disponibles
./restore_volume.sh

# Restaurer une sauvegarde spécifique
./restore_volume.sh backup_20241201_143022
```

### Nettoyage

#### `clean-docker.dev.sh`
Nettoyage des ressources Docker.

```bash
# Nettoyage avec confirmation
./clean-docker.dev.sh

# Nettoyage sans confirmation
./clean-docker.dev.sh --force

# Nettoyage complet (images, volumes, réseaux)
./clean-docker.dev.sh --all
```

#### `delete_volume-docker.sh`
Suppression des volumes Docker.

```bash
# Supprimer tous les volumes
./delete_volume-docker.sh
```

## 🛠️ Utilitaires

### `docker-utils.sh`
Script utilitaire central qui fournit :
- Auto-détection du fichier compose (`docker-compose.simple.yml`)
- Auto-détection du réseau (`rag-cgi-simple-network`)
- Auto-détection du service principal (`rag-cgi-api`)
- Fonctions d'affichage de configuration

### `test-auto-detection.sh`
Script de test pour vérifier que l'auto-détection fonctionne correctement.

```bash
# Tester l'auto-détection
./test-auto-detection.sh
```

### `help.sh`
Script d'aide interactif.

```bash
# Afficher l'aide
./help.sh
```

## 🌐 Accès au service

Une fois démarré, le service RAG CGI est accessible sur :
- **Interface Web** : http://localhost:8080
- **API REST** : http://localhost:8080/docs (documentation Swagger)
- **Health Check** : http://localhost:8080/health
- **Personnalités** : http://localhost:8080/personnalites

## 💡 Conseils d'utilisation

### Workflow de développement typique

1. **Première fois** :
   ```bash
   ./build-and-start.sh
   ```

2. **Développement quotidien** :
   ```bash
   ./start-docker.dev.sh
   ```

3. **Après modification du code** :
   ```bash
   ./restart-docker.dev.sh rag-cgi-api --rebuild
   ```

4. **Debugging** :
   ```bash
   ./logs-docker.dev.sh rag-cgi-api -f
   ./exec-docker.dev.sh rag-cgi-api bash
   ```

5. **Sauvegarde avant changement important** :
   ```bash
   ./backup_volume.sh
   ```

### Gestion des erreurs

- Si un script échoue, vérifiez les logs avec `./logs-docker.dev.sh`
- Pour un reset complet : `./clean-docker.dev.sh --all` puis `./build-and-start.sh`
- Pour restaurer une sauvegarde : `./restore_volume.sh`

### Performance

- Utilisez `./start-docker.dev.sh` pour le développement quotidien (plus rapide)
- Utilisez `./build-and-start.sh --force-rebuild` seulement quand nécessaire
- Nettoyez régulièrement avec `./clean-docker.dev.sh`

## 🔍 Auto-détection

Tous les scripts utilisent l'auto-détection pour :
- Trouver automatiquement le fichier `docker-compose.simple.yml`
- Détecter le nom du réseau Docker
- Identifier le service principal (`rag-cgi-api`)
- S'adapter aux changements de configuration

Cette fonctionnalité élimine le besoin de modifier manuellement les scripts lors des changements de configuration.

## 📞 Support

Pour toute question ou problème :
1. Vérifiez l'aide avec `./help.sh`
2. Testez l'auto-détection avec `./test-auto-detection.sh`
3. Consultez les logs avec `./logs-docker.dev.sh`

---

**Note** : Tous les scripts sont conçus pour fonctionner de manière autonome et détecter automatiquement votre configuration. Aucune modification manuelle n'est nécessaire.
