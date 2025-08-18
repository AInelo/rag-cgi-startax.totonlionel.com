# 🎭 Implémentation des Personnalités du Chatbot RAG CGI

Ce document explique l'implémentation technique des trois personnalités du chatbot RAG CGI.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Web/API                        │
│  (sélection personnalité + question)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service RAG                              │
│  (recherche sources + génération réponse)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Service de Personnalités                     │
│  (génération prompts système personnalisés)                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Service LLM Gemini                          │
│  (génération réponse avec prompt personnalisé)             │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Structure des Fichiers

```
app/
├── services/
│   ├── personnalite_service.py      # Service principal des personnalités
│   ├── rag_service.py               # Service RAG modifié pour personnalités
│   └── llm_service_gemini.py       # Service LLM modifié pour personnalités
├── config/
│   └── personnalite_config.py      # Configuration des paramètres
└── models/
    └── schemas.py                   # Modèles avec champ personnalite

tests/
├── test_personnalites.py            # Tests des personnalités
├── test_config.py                   # Tests de configuration
└── demo_personnalites.py            # Démonstration

docs/
└── PERSONNALITES.md                 # Documentation utilisateur
```

## 🔧 Composants Techniques

### 1. Service de Personnalités (`personnalite_service.py`)

**Responsabilités :**
- Gestion des trois personnalités (Expert, Expert CGI, Mathématicien)
- Génération des prompts système personnalisés
- Interface unifiée pour récupérer les prompts

**Classes principales :**
```python
class PersonnaliteType(Enum):
    EXPERT = "expert"
    EXPERT_CGI = "expert_cgi"
    MATHEMATICIEN = "mathematicien"

class PersonnaliteService:
    def get_prompt_system(self, personnalite: str) -> str
    def get_personnalite_info(self) -> Dict[str, str]
```

### 2. Configuration des Personnalités (`personnalite_config.py`)

**Responsabilités :**
- Paramètres de génération par personnalité
- Support des variables d'environnement
- Validation automatique des configurations

**Configuration par défaut :**
```python
DEFAULT_CONFIG = {
    "expert": {
        "temperature": 0.1,        # Réponses déterministes
        "max_tokens": 150,         # Réponses courtes
        "top_p": 0.9,
        "top_k": 40
    },
    "expert_cgi": {
        "temperature": 0.3,        # Équilibré
        "max_tokens": 1000,        # Réponses détaillées
        "top_p": 0.95,
        "top_k": 64
    },
    "mathematicien": {
        "temperature": 0.2,        # Précision mathématique
        "max_tokens": 800,         # Réponses techniques
        "top_p": 0.92,
        "top_k": 50
    }
}
```

### 3. Intégration LLM (`llm_service_gemini.py`)

**Modifications apportées :**
- Paramètre `personnalite` ajouté aux méthodes de génération
- Intégration du service de personnalités dans `_build_cgi_prompt`
- Support des prompts système personnalisés

**Signature modifiée :**
```python
def _build_cgi_prompt(self, 
                     user_query: str,
                     context_documents: Optional[List[Dict]] = None,
                     conversation_history: Optional[List[Dict]] = None,
                     system_prompt: Optional[str] = None,
                     personnalite: str = "expert_cgi") -> str:
```

### 4. Service RAG (`rag_service.py`)

**Modifications apportées :**
- Paramètre `personnalite` ajouté à `generate_response_stream`
- Transmission de la personnalité au service LLM
- Support des configurations personnalisées

**Signature modifiée :**
```python
async def generate_response_stream(self, 
                                 question: str, 
                                 sources: List[DocumentSource],
                                 temperature: float = 0.3,
                                 max_tokens: int = 1000,
                                 personnalite: str = "expert_cgi") -> AsyncGenerator[Dict[str, Any], None]:
```

### 5. API FastAPI (`main.py`)

**Modifications apportées :**
- Champ `personnalite` ajouté au modèle `QueryRequest`
- Endpoint `/personnalites` pour lister les personnalités disponibles
- Transmission de la personnalité dans les endpoints `/query` et `/query/stream`
- Interface web avec sélecteur de personnalité

**Nouveaux endpoints :**
```python
@app.get("/personnalites")
async def get_personnalites()

@app.post("/query")
async def query_cgi(request: QueryRequest)

@app.get("/query/stream")
async def stream_query(..., personnalite: str = Query("expert_cgi"))
```

## 🎯 Personnalités Implémentées

### 🧠 Expert
- **Objectif** : Réponses courtes et directes
- **Contraintes** : 2-3 phrases maximum
- **Style** : Factuel et professionnel
- **Cas d'usage** : Consultations rapides, questions simples

### 🏛️ Expert CGI
- **Objectif** : Réponses détaillées avec références
- **Contraintes** : Explications complètes et structurées
- **Style** : Académique et professionnel
- **Cas d'usage** : Étude approfondie, formation, conseils détaillés

### 🧮 Mathématicien
- **Objectif** : Formules mathématiques et calculs
- **Contraintes** : Notations KaTeX, exemples numériques
- **Style** : Technique et mathématique
- **Cas d'usage** : Calculs fiscaux, formules, analyse quantitative

## 🚀 Utilisation

### Via l'API REST

```bash
# Requête avec personnalité Expert
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le taux de TVA ?",
    "personnalite": "expert",
    "context_type": "fiscal",
    "max_sources": 3
  }'

# Requête avec personnalité Mathématicien
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculez la TVA sur 500 000 FCFA",
    "personnalite": "mathematicien",
    "context_type": "fiscal",
    "max_sources": 5
  }'
```

### Via l'Interface Web

1. Ouvrir http://localhost:8080
2. Sélectionner la personnalité dans le menu déroulant
3. Saisir la question
4. La réponse sera générée selon la personnalité choisie

### Via le Streaming SSE

```bash
curl -N "http://localhost:8080/query/stream?question=Quel%20est%20le%20taux%20de%20TVA&personnalite=expert"
```

## ⚙️ Configuration

### Variables d'environnement

```bash
# Personnalité par défaut
DEFAULT_PERSONNALITE=expert_cgi

# Températures personnalisées
EXPERT_TEMPERATURE=0.1
EXPERT_CGI_TEMPERATURE=0.3
MATHEMATICIEN_TEMPERATURE=0.2

# Max tokens personnalisés
EXPERT_MAX_TOKENS=150
EXPERT_CGI_MAX_TOKENS=1000
MATHEMATICIEN_MAX_TOKENS=800
```

### Fichier de configuration

```python
# app/config/personnalite_config.py
DEFAULT_CONFIG = {
    "expert": {
        "temperature": 0.1,
        "max_tokens": 150,
        "top_p": 0.9,
        "top_k": 40
    }
    # ... autres personnalités
}
```

## 🧪 Tests

### Tests des personnalités

```bash
# Test complet des personnalités
python3 test_personnalites.py

# Test de la configuration
python3 test_config.py

# Démonstration
python3 demo_personnalites.py
```

### Tests dans Docker

```bash
# Copier les tests dans le container
docker cp test_personnalites.py rag-cgi-api:/app/

# Exécuter les tests
docker exec -it rag-cgi-api python3 /app/test_personnalites.py
```

## 🔍 Monitoring et Logs

### Endpoints de monitoring

```bash
# Informations sur les personnalités
curl http://localhost:8080/personnalites

# Statistiques du service
curl http://localhost:8080/stats

# Health check
curl http://localhost:8080/health
```

### Logs

```bash
# Suivre les logs en temps réel
docker-compose logs -f rag-cgi-api

# Logs spécifiques aux personnalités
docker logs rag-cgi-api | grep -i personnalite
```

## 🎨 Personnalisation

### Ajouter une nouvelle personnalité

1. **Modifier l'enum `PersonnaliteType`**
```python
class PersonnaliteType(Enum):
    EXPERT = "expert"
    EXPERT_CGI = "expert_cgi"
    MATHEMATICIEN = "mathematicien"
    NOUVELLE = "nouvelle"  # Ajouter ici
```

2. **Ajouter la méthode de prompt**
```python
def _get_nouvelle_prompt(self) -> str:
    return """Votre prompt personnalisé ici..."""
```

3. **Mettre à jour le dictionnaire**
```python
self.personnalites = {
    PersonnaliteType.EXPERT: self._get_expert_prompt(),
    PersonnaliteType.EXPERT_CGI: self._get_expert_cgi_prompt(),
    PersonnaliteType.MATHEMATICIEN: self._get_mathematicien_prompt(),
    PersonnaliteType.NOUVELLE: self._get_nouvelle_prompt()  # Ajouter ici
}
```

4. **Ajouter la configuration**
```python
DEFAULT_CONFIG = {
    "expert": {...},
    "expert_cgi": {...},
    "mathematicien": {...},
    "nouvelle": {  # Ajouter ici
        "temperature": 0.4,
        "max_tokens": 600,
        "top_p": 0.93,
        "top_k": 55
    }
}
```

5. **Tester**
```bash
python3 test_personnalites.py
```

### Modifier les prompts existants

Éditer directement dans `app/services/personnalite_service.py` :

```python
def _get_expert_prompt(self) -> str:
    return """Votre nouveau prompt personnalisé..."""
```

## 🐛 Dépannage

### Problèmes courants

**Personnalité non reconnue :**
- Vérifier l'orthographe exacte : `expert`, `expert_cgi`, `mathematicien`
- Consulter `/personnalites` pour la liste complète
- Vérifier les logs pour les erreurs

**Réponses incohérentes :**
- Vérifier que la personnalité est bien passée dans la requête
- Consulter la configuration dans `personnalite_config.py`
- Vérifier les variables d'environnement

**Formules KaTeX non rendues :**
- S'assurer d'utiliser la personnalité "mathematicien"
- Vérifier que le frontend supporte KaTeX
- Consulter les logs pour les erreurs de génération

### Commandes de diagnostic

```bash
# Vérifier la configuration
python3 test_config.py

# Tester les personnalités
python3 test_personnalites.py

# Vérifier les endpoints
curl http://localhost:8080/personnalites
curl http://localhost:8080/health

# Logs en temps réel
docker-compose logs -f rag-cgi-api
```

## 📚 Documentation Complémentaire

- **PERSONNALITES.md** : Guide utilisateur des personnalités
- **README.md** : Documentation générale du projet
- **API docs** : Documentation automatique FastAPI sur `/docs`

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/NouvellePersonnalite`)
3. Implémentez la nouvelle personnalité
4. Ajoutez les tests correspondants
5. Committez vos changements (`git commit -m 'Add NouvellePersonnalite'`)
6. Push vers la branche (`git push origin feature/NouvellePersonnalite`)
7. Ouvrez une Pull Request

---

**Développé avec ❤️ pour simplifier l'accès au Code Général des Impôts du Bénin** 