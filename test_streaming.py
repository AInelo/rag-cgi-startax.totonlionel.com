#!/usr/bin/env python3
"""
Script de test pour l'endpoint de streaming SSE du service RAG CGI
"""

import requests
import json
import time

def test_streaming_endpoint():
    """Test de l'endpoint de streaming"""
    
    # URL de base
    base_url = "http://localhost:8080"
    
    # Test 1: Question simple sur la TVA
    print("🧪 Test 1: Question sur la TVA")
    print("=" * 50)
    
    question = "Quels sont les taux de TVA au Bénin ?"
    params = {
        "question": question,
        "context_type": "fiscal",
        "max_sources": 3
    }
    
    try:
        response = requests.get(
            f"{base_url}/query/stream",
            params=params,
            stream=True,
            headers={"Accept": "text/plain"}
        )
        
        if response.status_code == 200:
            print(f"✅ Connexion établie")
            print(f"📝 Question: {question}")
            print(f"🔍 Type de contexte: {params['context_type']}")
            print(f"📚 Sources max: {params['max_sources']}")
            print("\n📡 Réponse en streaming:")
            print("-" * 30)
            
            response_content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Enlever 'data: '
                            
                            if data.get('type') == 'search_start':
                                print("🔍 Recherche dans les documents...")
                            elif data.get('type') == 'sources_found':
                                print(f"📚 {data.get('count', 0)} sources trouvées")
                                print("📖 Sources:")
                                for i, source in enumerate(data.get('sources', [])[:2]):
                                    print(f"   {i+1}. {source.get('title', 'N/A')} (Score: {source.get('relevance_score', 0):.3f})")
                                print("🤖 Génération de la réponse...")
                            elif data.get('type') == 'response_start':
                                print("💬 Réponse:")
                            elif data.get('type') == 'response_chunk':
                                content = data.get('content', '')
                                response_content += content
                                print(content, end='', flush=True)
                            elif data.get('type') == 'response_complete':
                                metadata = data.get('metadata', {})
                                print(f"\n\n✅ Réponse complète!")
                                print(f"⏱️  Temps de traitement: {metadata.get('processing_time', 0):.2f}s")
                                print(f"🎯 Score de confiance: {metadata.get('confidence', 0):.3f}")
                                print(f"🔤 Tokens utilisés: {metadata.get('tokens_used', 0)}")
                                break
                            elif data.get('type') == 'error':
                                print(f"❌ Erreur: {data.get('message', 'Erreur inconnue')}")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Erreur parsing JSON: {e}")
                            continue
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")

def test_multiple_questions():
    """Test avec plusieurs questions"""
    
    questions = [
        "Quels sont les taux d'imposition sur les revenus locatifs ?",
        "Comment déclarer une plus-value immobilière ?",
        "Quelles sont les déductions possibles pour un auto-entrepreneur ?",
        "Quel est le taux de l'Impôt sur les Bénéfices Agricoles (IBA) ?"
    ]
    
    print("\n🧪 Test 2: Questions multiples")
    print("=" * 50)
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 40)
        
        params = {
            "question": question,
            "context_type": "fiscal",
            "max_sources": 2
        }
        
        try:
            response = requests.get(
                "http://localhost:8080/query/stream",
                params=params,
                stream=True,
                headers={"Accept": "text/plain"}
            )
            
            if response.status_code == 200:
                response_content = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                
                                if data.get('type') == 'response_chunk':
                                    content = data.get('content', '')
                                    response_content += content
                                elif data.get('type') == 'response_complete':
                                    metadata = data.get('metadata', {})
                                    print(f"✅ Réponse: {response_content[:100]}...")
                                    print(f"⏱️  Temps: {metadata.get('processing_time', 0):.2f}s")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
        
        time.sleep(1)  # Pause entre les questions

if __name__ == "__main__":
    print("🚀 Test du service RAG CGI - Streaming SSE")
    print("=" * 60)
    
    # Test 1: Question détaillée
    test_streaming_endpoint()
    
    # Test 2: Questions multiples
    test_multiple_questions()
    
    print("\n🎉 Tests terminés!")
    print("🌐 Interface web: http://localhost:8080")
    print("📊 Health check: http://localhost:8080/health") 