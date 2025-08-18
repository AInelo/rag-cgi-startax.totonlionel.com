#!/usr/bin/env python3
"""
Script de test pour le système RAG CGI
Teste différentes requêtes sur le Code Général des Impôts du Bénin
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
HEADERS = {"Content-Type": "application/json"}

def test_health():
    """Test de l'endpoint de santé"""
    print("🏥 Test de santé du service...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service en bonne santé")
            print(f"   - Statut: {data['status']}")
            print(f"   - Documents indexés: {data['documents_indexed']}")
            print(f"   - Service RAG: {data['rag_service']}")
            return True
        else:
            print(f"❌ Erreur de santé: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_query(question, max_sources=3, context_type="general"):
    """Test d'une requête RAG"""
    print(f"\n🔍 Test de requête: {question}")
    print(f"   - Sources max: {max_sources}")
    print(f"   - Contexte: {context_type}")
    
    payload = {
        "question": question,
        "max_sources": max_sources,
        "context_type": context_type
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/query", headers=HEADERS, json=payload)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Réponse reçue en {processing_time:.2f}s")
            print(f"   - Succès: {data['success']}")
            print(f"   - Score de confiance: {data['confidence_score']:.1%}")
            print(f"   - Tokens utilisés: {data['tokens_used']}")
            print(f"   - Sources trouvées: {len(data['sources'])}")
            
            # Afficher la réponse
            print(f"\n📝 Réponse:")
            print(f"{data['answer'][:300]}...")
            
            # Afficher les sources
            if data['sources']:
                print(f"\n📚 Sources:")
                for i, source in enumerate(data['sources'][:2], 1):
                    print(f"   {i}. Score: {source['relevance_score']:.2f}")
                    print(f"      Contenu: {source['content'][:100]}...")
            
            return True
        else:
            print(f"❌ Erreur de requête: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test du système RAG CGI - Code Général des Impôts du Bénin")
    print("=" * 70)
    print(f"⏰ Début des tests: {datetime.now().strftime('%H:%M:%S')}")
    
    # Test de santé
    if not test_health():
        print("❌ Service non disponible, arrêt des tests")
        return
    
    # Requêtes de test
    test_queries = [
        {
            "question": "Quels sont les taux de TVA applicables au Bénin ?",
            "max_sources": 2,
            "context_type": "fiscal"
        },
        {
            "question": "Quelles sont les obligations fiscales pour une entreprise au Bénin ?",
            "max_sources": 3,
            "context_type": "entreprise"
        },
        {
            "question": "Comment fonctionne la taxe sur les véhicules à moteur ?",
            "max_sources": 2,
            "context_type": "general"
        },
        {
            "question": "Quels sont les impôts sur les assurances au Bénin ?",
            "max_sources": 2,
            "context_type": "fiscal"
        }
    ]
    
    # Exécuter les tests
    success_count = 0
    total_count = len(test_queries)
    
    for i, query_info in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}/{total_count}")
        print(f"{'='*50}")
        
        if test_query(**query_info):
            success_count += 1
        
        # Pause entre les requêtes
        if i < total_count:
            print("\n⏳ Pause de 2 secondes...")
            time.sleep(2)
    
    # Résumé des tests
    print(f"\n{'='*70}")
    print(f"📊 Résumé des tests: {success_count}/{total_count} réussis")
    print(f"⏰ Fin des tests: {datetime.now().strftime('%H:%M:%S')}")
    
    if success_count == total_count:
        print("🎉 Tous les tests ont réussi !")
    else:
        print(f"⚠️  {total_count - success_count} test(s) ont échoué")

if __name__ == "__main__":
    main() 