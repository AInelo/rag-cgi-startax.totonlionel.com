#!/usr/bin/env python3
"""
Démonstration simple du système RAG CGI
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_simple():
    """Test simple du système"""
    print("🚀 Démonstration du système RAG CGI")
    print("=" * 50)
    
    # Test de santé
    print("\n🏥 Test de santé...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service opérationnel")
            print(f"   Documents indexés: {data['documents_indexed']}")
        else:
            print(f"❌ Erreur: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # Test de requête simple
    print("\n🔍 Test de requête simple...")
    payload = {
        "question": "Que contient le Code Général des Impôts du Bénin ?",
        "max_sources": 2,
        "context_type": "general"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/query", 
                               headers={"Content-Type": "application/json"}, 
                               json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Réponse reçue")
            print(f"   Succès: {data['success']}")
            print(f"   Confiance: {data['confidence_score']:.1%}")
            print(f"   Sources: {len(data['sources'])}")
            
            if data['sources']:
                print(f"\n📚 Première source:")
                source = data['sources'][0]
                print(f"   Score: {source['relevance_score']:.2f}")
                print(f"   Contenu: {source['content'][:200]}...")
            
            print(f"\n📝 Réponse complète:")
            print(data['answer'])
            
        else:
            print(f"❌ Erreur de requête: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print(f"\n🌐 Interface web: {BASE_URL}")
    print("=" * 50)

if __name__ == "__main__":
    test_simple() 