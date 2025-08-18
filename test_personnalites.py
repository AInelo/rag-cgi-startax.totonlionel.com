#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des personnalités du chatbot RAG CGI
"""

import asyncio
import sys
import os

# Ajouter le répertoire app au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.personnalite_service import PersonnaliteService
from app.services.llm_service_gemini import GeminiLLMService

async def test_personnalites():
    """Test des différentes personnalités du chatbot"""
    
    print("🧪 Test des Personnalités du Chatbot RAG CGI")
    print("=" * 50)
    
    # Test du service de personnalités
    print("\n1. Test du service de personnalités...")
    try:
        personnalite_service = PersonnaliteService()
        personnalites = personnalite_service.get_personnalite_info()
        
        for key, info in personnalites.items():
            print(f"   ✅ {key}: {info['nom']} - {info['description']}")
        
        print("\n2. Test des prompts système...")
        for personnalite in ["expert", "expert_cgi", "mathematicien"]:
            prompt = personnalite_service.get_prompt_system(personnalite)
            print(f"   📝 {personnalite}: {len(prompt)} caractères")
            print(f"      Début: {prompt[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Erreur service personnalités: {e}")
        return
    
    # Test avec le service LLM (si disponible)
    print("\n3. Test avec le service LLM...")
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("   ⚠️  GOOGLE_API_KEY non définie, test LLM ignoré")
            return
        
        llm_service = GeminiLLMService(api_key=api_key)
        
        # Test de construction de prompt avec personnalité
        test_question = "Quel est le taux de TVA au Bénin ?"
        test_context = [{"content": "La TVA au Bénin est de 18% selon l'article X du CGI.", "source": "test", "score": 0.9}]
        
        for personnalite in ["expert", "expert_cgi", "mathematicien"]:
            print(f"\n   🧠 Test personnalité: {personnalite}")
            
            prompt = llm_service._build_cgi_prompt(
                user_query=test_question,
                context_documents=test_context,
                personnalite=personnalite
            )
            
            print(f"      Longueur prompt: {len(prompt)} caractères")
            print(f"      Contient personnalité: {'✅' if personnalite in prompt.lower() else '❌'}")
            
            # Vérifier que le prompt contient les instructions spécifiques
            if personnalite == "expert":
                assert "COURTES" in prompt, "Prompt expert doit contenir 'COURTES'"
            elif personnalite == "expert_cgi":
                assert "DÉTAILLÉES" in prompt, "Prompt expert_cgi doit contenir 'DÉTAILLÉES'"
            elif personnalite == "mathematicien":
                assert "KaTeX" in prompt, "Prompt mathematicien doit contenir 'KaTeX'"
            
            print(f"      ✅ Validation prompt {personnalite}")
        
        print("\n   🎯 Tous les tests de prompts sont passés !")
        
    except Exception as e:
        print(f"   ❌ Erreur test LLM: {e}")

def test_exemples_questions():
    """Test avec des exemples de questions typiques"""
    
    print("\n4. Exemples de questions pour chaque personnalité...")
    
    exemples = {
        "expert": [
            "Quel est le taux de TVA au Bénin ?",
            "Qu'est-ce que l'IS ?",
            "Comment déclarer mes revenus ?"
        ],
        "expert_cgi": [
            "Expliquez en détail le régime fiscal des entreprises au Bénin avec références aux articles du CGI",
            "Quelles sont les conditions d'exonération de l'impôt sur les sociétés selon le Code Général des Impôts ?",
            "Décrivez le processus de déclaration et de paiement de la TVA pour une entreprise béninoise"
        ],
        "mathematicien": [
            "Donnez la formule de calcul de l'impôt sur les sociétés avec un exemple numérique",
            "Calculez la TVA sur une facture de 500 000 FCFA HT",
            "Quelle est la relation mathématique pour le calcul de l'impôt sur le revenu des personnes physiques ?"
        ]
    }
    
    for personnalite, questions in exemples.items():
        print(f"\n   🎭 {personnalite.upper()}:")
        for i, question in enumerate(questions, 1):
            print(f"      {i}. {question}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests des personnalités...")
    
    # Test synchrone
    test_exemples_questions()
    
    # Test asynchrone
    asyncio.run(test_personnalites())
    
    print("\n🎉 Tests terminés !")
    print("\n📋 Résumé des personnalités disponibles:")
    print("   • expert: Réponses courtes et directes")
    print("   • expert_cgi: Réponses détaillées avec références CGI")
    print("   • mathematicien: Formules mathématiques en KaTeX")
    
    print("\n💡 Pour tester en ligne:")
    print("   1. Démarrez le serveur: docker-compose up")
    print("   2. Ouvrez: http://localhost:8080")
    print("   3. Sélectionnez une personnalité et posez une question") 