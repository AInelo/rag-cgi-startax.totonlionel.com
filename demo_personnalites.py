#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démonstration des Personnalités du Chatbot RAG CGI
"""

import sys
import os

# Ajouter le répertoire app au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def demo_personnalites():
    """Démonstration des personnalités disponibles"""
    
    print("🎭 DÉMONSTRATION DES PERSONNALITÉS DU CHATBOT RAG CGI")
    print("=" * 60)
    
    try:
        from app.services.personnalite_service import PersonnaliteService
        
        # Créer le service
        ps = PersonnaliteService()
        
        # Afficher les informations
        print("\n📋 PERSONNALITÉS DISPONIBLES:")
        print("-" * 40)
        
        personnalites = ps.get_personnalite_info()
        for key, info in personnalites.items():
            print(f"🔹 {key.upper()}")
            print(f"   Nom: {info['nom']}")
            print(f"   Description: {info['description']}")
            print(f"   Style: {info['style']}")
            print()
        
        # Afficher un exemple de prompt pour chaque personnalité
        print("📝 EXEMPLES DE PROMPTS SYSTÈME:")
        print("-" * 40)
        
        for personnalite in ["expert", "expert_cgi", "mathematicien"]:
            print(f"\n🎯 {personnalite.upper()}:")
            prompt = ps.get_prompt_system(personnalite)
            
            # Extraire les mots-clés caractéristiques
            if personnalite == "expert":
                keywords = ["COURTES", "DIRECTES", "2-3 phrases"]
            elif personnalite == "expert_cgi":
                keywords = ["DÉTAILLÉES", "RÉFÉRENCES", "EXPLICATIONS"]
            elif personnalite == "mathematicien":
                keywords = ["KaTeX", "FORMULES", "MATHÉMATIQUES"]
            
            print(f"   Mots-clés: {', '.join(keywords)}")
            print(f"   Longueur: {len(prompt)} caractères")
            print(f"   Début: {prompt[:100]}...")
        
        print("\n✅ Service de personnalités fonctionnel !")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Assurez-vous que le service est correctement installé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def demo_utilisation():
    """Démonstration de l'utilisation des personnalités"""
    
    print("\n🚀 GUIDE D'UTILISATION:")
    print("-" * 30)
    
    print("""
1. 🎯 CHOISIR LA PERSONNALITÉ:
   - expert: Pour des réponses rapides et factuelles
   - expert_cgi: Pour des explications détaillées avec références
   - mathematicien: Pour des formules et calculs mathématiques

2. 📝 POSER LA QUESTION:
   - Via l'interface web: http://localhost:8080
   - Via l'API REST: POST /query avec paramètre personnalite
   - Via le streaming: GET /query/stream avec paramètre personnalite

3. 🔍 EXEMPLE DE REQUÊTE:
   curl -X POST http://localhost:8080/query \\
     -H "Content-Type: application/json" \\
     -d '{
       "question": "Quel est le taux de TVA au Bénin ?",
       "personnalite": "expert",
       "context_type": "fiscal",
       "max_sources": 3
     }'

4. 🎭 COMPARAISON DES RÉPONSES:
   - Même question, personnalités différentes = réponses différentes
   - Chaque personnalité respecte ses contraintes de style
   - La personnalité influence la longueur et le détail de la réponse
""")

def demo_exemples():
    """Exemples de questions pour chaque personnalité"""
    
    print("\n💡 EXEMPLES DE QUESTIONS PAR PERSONNALITÉ:")
    print("-" * 50)
    
    exemples = {
        "expert": [
            "Quel est le taux de TVA au Bénin ?",
            "Qu'est-ce que l'impôt sur les sociétés ?",
            "Comment s'appelle l'impôt sur les revenus ?"
        ],
        "expert_cgi": [
            "Expliquez en détail le régime fiscal des entreprises au Bénin avec références aux articles du CGI",
            "Quelles sont les conditions d'exonération de l'IS selon le Code Général des Impôts ?",
            "Décrivez le processus de déclaration et de paiement de la TVA"
        ],
        "mathematicien": [
            "Donnez la formule de calcul de l'impôt sur les sociétés avec un exemple numérique",
            "Calculez la TVA sur une facture de 500 000 FCFA HT",
            "Quelle est la relation mathématique pour le calcul de l'IRPP ?"
        ]
    }
    
    for personnalite, questions in exemples.items():
        print(f"\n🎭 {personnalite.upper()}:")
        for i, question in enumerate(questions, 1):
            print(f"   {i}. {question}")
    
    print("\n💡 CONSEIL: Testez la même question avec différentes personnalités pour voir la différence !")

if __name__ == "__main__":
    print("🎬 DÉMARRAGE DE LA DÉMONSTRATION...")
    
    # Démonstration des personnalités
    demo_personnalites()
    
    # Guide d'utilisation
    demo_utilisation()
    
    # Exemples de questions
    demo_exemples()
    
    print("\n🎉 DÉMONSTRATION TERMINÉE !")
    print("\n📚 Pour plus d'informations, consultez PERSONNALITES.md")
    print("🧪 Pour tester, lancez: python3 test_personnalites.py")
    print("🌐 Pour l'interface web: docker-compose up puis http://localhost:8080") 