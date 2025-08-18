#!/usr/bin/env python3
"""
Script de diagnostic pour le système RAG CGI
Vérifie l'état de l'indexation et de la recherche
"""

import asyncio
import os
import sys
import pickle
from pathlib import Path

# Ajouter le répertoire app au path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.rag_service import RAGService
from app.database.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService

async def diagnostic_complet():
    """Diagnostic complet du système RAG"""
    print("🔍 DIAGNOSTIC COMPLET DU SYSTÈME RAG CGI")
    print("=" * 60)
    
    # 1. Vérifier la configuration
    print("\n📋 1. CONFIGURATION")
    print("-" * 30)
    
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if api_key:
        print(f"✅ Clé API Google trouvée: {api_key[:10]}...")
    else:
        print("❌ Aucune clé API Google trouvée")
        print("   Définissez GOOGLE_API_KEY dans votre environnement")
    
    # 2. Vérifier les documents source
    print("\n📚 2. DOCUMENTS SOURCE")
    print("-" * 30)
    
    data_dir = Path("./data/cgi_documents")
    if data_dir.exists():
        documents = list(data_dir.glob("*.md"))
        print(f"✅ Dossier data trouvé: {len(documents)} documents Markdown")
        for doc in documents:
            size_mb = doc.stat().st_size / (1024 * 1024)
            print(f"   📄 {doc.name}: {size_mb:.1f} MB")
    else:
        print("❌ Dossier data/cgi_documents non trouvé")
    
    # 3. Vérifier la base vectorielle
    print("\n🗄️ 3. BASE VECTORIELLE")
    print("-" * 30)
    
    vector_db_path = Path("./vector_db/cgi_documents.pkl")
    if vector_db_path.exists():
        size_mb = vector_db_path.stat().st_size / (1024 * 1024)
        print(f"✅ Base vectorielle trouvée: {size_mb:.1f} MB")
        
        # Charger et analyser la base
        try:
            with open(vector_db_path, 'rb') as f:
                data = pickle.load(f)
            
            documents = data.get("documents", {})
            embeddings = data.get("embeddings", [])
            document_ids = data.get("document_ids", [])
            
            print(f"   📊 {len(documents)} documents indexés")
            print(f"   🔢 {len(embeddings)} embeddings")
            print(f"   🆔 {len(document_ids)} IDs de documents")
            
            if embeddings:
                embedding_dim = len(embeddings[0])
                print(f"   📏 Dimension des embeddings: {embedding_dim}")
            
            # Afficher quelques exemples de documents
            if documents:
                print("\n   📝 Exemples de documents indexés:")
                for i, (doc_id, doc) in enumerate(list(documents.items())[:3]):
                    content_preview = doc.get("content", "")[:100] + "..."
                    print(f"      {i+1}. {doc_id}: {content_preview}")
                    
        except Exception as e:
            print(f"   ❌ Erreur lecture base vectorielle: {e}")
    else:
        print("❌ Base vectorielle non trouvée")
        print("   Lancez l'indexation avec: python -m app.main")
    
    # 4. Test du service d'embeddings
    print("\n🧠 4. SERVICE D'EMBEDDINGS")
    print("-" * 30)
    
    if api_key:
        try:
            embedding_service = EmbeddingService(api_key)
            test_text = "Test d'embedding pour diagnostic"
            embedding = await embedding_service.get_embedding(test_text)
            
            if embedding:
                print(f"✅ Service d'embeddings fonctionnel")
                print(f"   📏 Dimension: {len(embedding)}")
                print(f"   🔢 Valeurs: {embedding[:3]}...")
            else:
                print("❌ Service d'embeddings ne retourne pas d'embedding")
        except Exception as e:
            print(f"❌ Erreur service d'embeddings: {e}")
    else:
        print("⚠️ Impossible de tester le service d'embeddings sans clé API")
    
    # 5. Test de recherche
    print("\n🔍 5. TEST DE RECHERCHE")
    print("-" * 30)
    
    if vector_db_path.exists() and api_key:
        try:
            # Initialiser le service RAG
            rag_service = RAGService(api_key)
            await rag_service.initialize()
            
            # Test de recherche
            test_question = "Quels sont les taux de TVA au Bénin ?"
            print(f"   🧪 Question test: {test_question}")
            
            sources = await rag_service.search_relevant_sources(
                question=test_question,
                max_sources=3,
                context_type="fiscal"
            )
            
            print(f"   📚 Sources trouvées: {len(sources)}")
            
            if sources:
                for i, source in enumerate(sources[:2]):
                    print(f"      {i+1}. Score: {source.relevance_score:.3f}")
                    print(f"         Contenu: {source.content[:100]}...")
            else:
                print("   ❌ Aucune source trouvée")
                
        except Exception as e:
            print(f"   ❌ Erreur test de recherche: {e}")
    else:
        print("⚠️ Impossible de tester la recherche")
    
    # 6. Recommandations
    print("\n💡 6. RECOMMANDATIONS")
    print("-" * 30)
    
    if not api_key:
        print("🔑 Définissez GOOGLE_API_KEY dans votre environnement")
        print("   export GOOGLE_API_KEY='votre_clé_api'")
    
    if not vector_db_path.exists():
        print("📚 Lancez l'indexation des documents")
        print("   python -m app.main")
    
    if vector_db_path.exists() and api_key:
        print("✅ Système RAG prêt pour les tests")
        print("   Testez avec: python test_streaming.py")
    
    print("\n" + "=" * 60)
    print("🏁 Diagnostic terminé")

if __name__ == "__main__":
    asyncio.run(diagnostic_complet()) 