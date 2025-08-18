# ==============================================================================
# FILE: app/services/embedding_service.py - Service d'Embeddings Google API
# ==============================================================================

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional
import json
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Configuration de l'API Google
        genai.configure(api_key=api_key)
        self.embedding_model = "models/text-embedding-004"
        
    async def _make_embedding_request(self, texts: List[str]) -> List[List[float]]:
        """Fait une requête à l'API Google pour les embeddings"""
        embeddings = []
        
        try:
            for text in texts:
                # Utilisation de l'API Google pour les embeddings
                result = genai.embed_content(
                    model=self.embedding_model,
                    content=text
                )
                embedding = result["embedding"]
                embeddings.append(embedding)
                
            logger.info(f"✅ {len(embeddings)} embeddings générés via Google API")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la requête d'embedding Google: {str(e)}")
            # Fallback: embeddings aléatoires (pour le développement)
            return self._generate_fallback_embeddings(texts)
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings de fallback pour le développement"""
        logger.warning("⚠️ Utilisation d'embeddings de fallback (développement uniquement)")
        embeddings = []
        for text in texts:
            # Embedding aléatoire de dimension 768 (comme text-embedding-004)
            embedding = np.random.normal(0, 1, 768).tolist()
            embeddings.append(embedding)
        return embeddings
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Récupère les embeddings pour une liste de textes"""
        if not texts:
            return []
        
        try:
            embeddings = await self._make_embedding_request(texts)
            return embeddings
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération des embeddings: {str(e)}")
            return self._generate_fallback_embeddings(texts)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Récupère l'embedding pour un seul texte"""
        embeddings = await self.get_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux embeddings"""
        try:
            # Convertir en arrays numpy
            emb1 = np.array(embedding1).reshape(1, -1)
            emb2 = np.array(embedding2).reshape(1, -1)
            
            # Calculer la similarité cosinus
            similarity = cosine_similarity(emb1, emb2)[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Erreur lors du calcul de similarité: {str(e)}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                              candidate_embeddings: List[List[float]], 
                          top_k: int = 5) -> List[tuple]:
        """Trouve les embeddings les plus similaires"""
        try:
            similarities = []
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate)
                similarities.append((i, similarity))
        
            # Trier par similarité décroissante
            similarities.sort(key=lambda x: x[1], reverse=True)
        
            # Retourner les top_k
            return similarities[:top_k]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de similarité: {str(e)}")
            return []
    
    async def cleanup(self):
        """Nettoie les ressources"""
        logger.info("🧹 Service d'embeddings Google nettoyé")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le modèle d'embedding"""
        return {
            "model": self.embedding_model,
            "api_provider": "Google AI",
            "embedding_dimension": 768,
            "fallback_mode": "random_embeddings"
        }