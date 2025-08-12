# ==============================================================================
# FILE: app/services/embedding_service.py - Service d'Embeddings Ultra-Léger
# ==============================================================================

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional
import aiohttp
import json
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"
        self.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        self.session = None
        
    async def _get_session(self):
        """Crée une session HTTP réutilisable"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_embedding_request(self, texts: List[str]) -> List[List[float]]:
        """Fait une requête à l'API Hugging Face pour les embeddings"""
        url = f"{self.base_url}/{self.embedding_model}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": texts
        }
        
        session = await self._get_session()
        
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    # L'API retourne une liste d'embeddings
                    if isinstance(result, list):
                        return result
                    else:
                        # Format alternatif
                        return [result.get("embedding", [])]
                else:
                    error_text = await response.text()
                    logger.error(f"Erreur API Hugging Face: {response.status} - {error_text}")
                    # Fallback: embeddings aléatoires (pour le développement)
                    return self._generate_fallback_embeddings(texts)
        except Exception as e:
            logger.error(f"Erreur lors de la requête d'embedding: {str(e)}")
            # Fallback: embeddings aléatoires
            return self._generate_fallback_embeddings(texts)
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings de fallback pour le développement"""
        logger.warning("⚠️ Utilisation d'embeddings de fallback (développement uniquement)")
        embeddings = []
        for text in texts:
            # Embedding aléatoire de dimension 384 (comme all-MiniLM-L6-v2)
            embedding = np.random.normal(0, 1, 384).tolist()
            embeddings.append(embedding)
        return embeddings
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Récupère les embeddings pour une liste de textes"""
        if not texts:
            return []
        
        try:
            embeddings = await self._make_embedding_request(texts)
            logger.info(f"✅ Embeddings générés pour {len(texts)} textes")
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
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("🧹 Service d'embeddings nettoyé")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le modèle d'embedding"""
        return {
            "model": self.embedding_model,
            "api_provider": "Hugging Face",
            "embedding_dimension": 384,
            "fallback_mode": "random_embeddings"
        }