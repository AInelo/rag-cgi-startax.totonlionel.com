# 🎭 Personnalités du Chatbot RAG CGI

Ce document explique les trois personnalités disponibles pour votre chatbot RAG CGI et comment les utiliser efficacement.

## 🧠 Personnalité 1: Expert

**Caractéristiques :**
- **Style** : Réponses courtes et directes
- **Longueur** : 2-3 phrases maximum
- **Objectif** : Réponses factuelles et précises
- **Public** : Utilisateurs pressés, consultations rapides

**Exemple de réponse :**
```
Question : "Quel est le taux de TVA standard au Bénin ?"
Réponse : "Le taux de TVA standard au Bénin est de 18% selon l'article X du CGI."
```

**Quand l'utiliser :**
- Questions simples et directes
- Consultations rapides
- Besoin d'informations factuelles uniquement
- Temps limité

---

## 🏛️ Personnalité 2: Expert CGI

**Caractéristiques :**
- **Style** : Réponses détaillées avec références complètes
- **Longueur** : Explications complètes et structurées
- **Objectif** : Compréhension approfondie du CGI
- **Public** : Professionnels, étudiants, consultations détaillées

**Exemple de réponse :**
```
Question : "Expliquez le régime fiscal des entreprises au Bénin"

Réponse : "Le régime fiscal des entreprises au Bénin est défini par le Code Général des Impôts (CGI) et comprend plusieurs composants :

1. **Impôt sur les Sociétés (IS)** : Selon l'article X du CGI, l'IS s'applique aux bénéfices des sociétés à un taux de 30%.

2. **TVA** : La Taxe sur la Valeur Ajoutée est fixée à 18% selon l'article Y, avec des régimes spéciaux pour certaines activités.

3. **Déclarations** : Les entreprises doivent déclarer leurs revenus trimestriellement selon les modalités définies dans la section Z.

**Références CGI :** Articles X, Y, Z - Sections correspondantes

**Note :** Pour des conseils fiscaux personnalisés, consultez un expert-comptable agréé."
```

**Quand l'utiliser :**
- Questions complexes nécessitant des explications détaillées
- Besoin de références précises aux articles du CGI
- Étude ou analyse approfondie
- Formation et apprentissage

---

## 🧮 Personnalité 3: Mathématicien

**Caractéristiques :**
- **Style** : Formules mathématiques en format KaTeX
- **Longueur** : Explications techniques avec calculs
- **Objectif** : Compréhension des relations arithmétiques
- **Public** : Comptables, analystes financiers, étudiants en mathématiques

**Exemple de réponse :**
```
Question : "Comment calculer la TVA sur une facture ?"

Réponse : "La TVA se calcule selon la formule mathématique suivante :

$$TVA = Base \times 0.18$$

Où :
- $TVA$ = Montant de la TVA à payer
- $Base$ = Montant hors taxes (HT)
- $0.18$ = Taux de TVA (18% = 0.18)

**Exemple de calcul :**
Pour une facture de 100 000 FCFA HT :
$$TVA = 100\,000 \times 0.18 = 18\,000 \text{ FCFA}$$

**Montant TTC :**
$$TTC = Base + TVA = 100\,000 + 18\,000 = 118\,000 \text{ FCFA}$$

**Référence CGI :** Article X - Calcul de la TVA"
```

**Quand l'utiliser :**
- Questions impliquant des calculs fiscaux
- Besoin de formules mathématiques précises
- Analyse quantitative des impôts
- Vérification de calculs

---

## 🎯 Comment Choisir la Bonne Personnalité

### 🔍 Questions Simples → Expert
- "Quel est le taux de l'IS ?"
- "Qu'est-ce que la TVA ?"
- "Comment s'appelle l'impôt sur les revenus ?"

### 📚 Questions Complexes → Expert CGI
- "Expliquez le processus de déclaration fiscale"
- "Quelles sont les conditions d'exonération ?"
- "Décrivez le régime fiscal des PME"

### 🧮 Questions de Calcul → Mathématicien
- "Calculez l'impôt sur un revenu de X FCFA"
- "Quelle est la formule de calcul de la TVA ?"
- "Comment déterminer l'assiette imposable ?"

---

## 🚀 Utilisation Technique

### Via l'API

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

1. Ouvrez http://localhost:8080
2. Sélectionnez la personnalité dans le menu déroulant
3. Posez votre question
4. La réponse sera générée selon la personnalité choisie

---

## 🔧 Configuration Avancée

### Variables d'environnement

```bash
# Personnalité par défaut
DEFAULT_PERSONNALITE=expert_cgi

# Température par personnalité
EXPERT_TEMPERATURE=0.1        # Réponses plus déterministes
EXPERT_CGI_TEMPERATURE=0.3    # Équilibré
MATHEMATICIEN_TEMPERATURE=0.2 # Précision mathématique
```

### Personnalisation des prompts

Vous pouvez modifier les prompts système dans `app/services/personnalite_service.py` :

```python
def _get_expert_prompt(self) -> str:
    return """Votre prompt personnalisé ici..."""
```

---

## 📊 Comparaison des Personnalités

| Aspect | Expert | Expert CGI | Mathématicien |
|--------|--------|------------|---------------|
| **Longueur** | Court | Long | Moyen |
| **Détail** | Minimal | Maximal | Technique |
| **Références** | Basiques | Complètes | Spécifiques |
| **Calculs** | Aucun | Exemples | Formules KaTeX |
| **Temps** | Rapide | Modéré | Modéré |
| **Précision** | Élevée | Très élevée | Technique |

---

## 🧪 Tests et Validation

### Test des personnalités

```bash
# Exécuter les tests
python3 test_personnalites.py

# Test spécifique
docker exec -it rag-cgi-api python3 /app/test_personnalites.py
```

### Validation des réponses

Chaque personnalité doit respecter ses contraintes :

- **Expert** : Réponses ≤ 3 phrases
- **Expert CGI** : Références aux articles du CGI
- **Mathématicien** : Formules en format KaTeX

---

## 🎨 Personnalisation Avancée

### Ajouter une nouvelle personnalité

1. Modifiez `PersonnaliteType` enum
2. Ajoutez la méthode `_get_nouvelle_personnalite_prompt()`
3. Mettez à jour le dictionnaire `personnalites`
4. Testez avec `test_personnalites.py`

### Intégration avec d'autres modèles

Les personnalités sont compatibles avec tous les modèles Gemini :
- gemini-2.0-flash
- gemini-1.5-flash
- gemini-1.5-pro
- gemma-3

---

## 📞 Support et Dépannage

### Problèmes courants

**Personnalité non reconnue :**
- Vérifiez l'orthographe : `expert`, `expert_cgi`, `mathematicien`
- Consultez `/personnalites` pour la liste complète

**Réponses incohérentes :**
- Vérifiez que la personnalité est bien passée dans la requête
- Consultez les logs pour identifier le problème

**Formules KaTeX non rendues :**
- Assurez-vous d'utiliser la personnalité "mathematicien"
- Vérifiez que le frontend supporte KaTeX

### Logs et monitoring

```bash
# Suivre les logs en temps réel
docker-compose logs -f rag-cgi-api

# Vérifier les requêtes
curl http://localhost:8080/stats
```

---

## 🎯 Bonnes Pratiques

1. **Choisissez la personnalité selon le besoin** : Ne demandez pas une formule mathématique à l'Expert
2. **Utilisez des questions claires** : Plus la question est précise, meilleure sera la réponse
3. **Vérifiez les sources** : Consultez toujours les références CGI fournies
4. **Testez différentes personnalités** : Comparez les réponses pour la même question
5. **Respectez le contexte** : Utilisez le bon type de contexte (fiscal, entreprise, particulier)

---

**Développé avec ❤️ pour simplifier l'accès au Code Général des Impôts du Bénin** 