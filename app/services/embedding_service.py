# ==============================================================================
# FILE: app/services/embedding_service.py - Service Embeddings avec Hugging Face
# ==============================================================================

import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None, use_local: bool = True):
        """
        Service d'embeddings avec option local ou API Hugging Face
        
        Args:
            api_key: Clé API Hugging Face (optionnel si use_local=True)
            use_local: Utiliser un modèle local (plus rapide et gratuit)
        """
        self.api_key = api_key
        self.use_local = use_local
        self.base_url = "https://api-inference.huggingface.co/pipeline/feature-extraction"
        
        # Modèles disponibles (du plus performant au plus rapide)
        self.models = {
            "multilingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "french": "dangvantuan/sentence-camembert-large",
            "fast": "sentence-transformers/all-MiniLM-L6-v2",
            "legal": "nlpaueb/legal-bert-base-uncased"  # Spécialisé juridique
        }
        
        self.current_model = "multilingual"  # Bon pour le français juridique
        self.local_model = None
        self.embedding_cache = {}  # Cache simple en mémoire
        
    async def initialize(self):
        """Initialise le service d'embeddings"""
        if self.use_local:
            try:
                logger.info(f"🔄 Chargement du modèle local: {self.models[self.current_model]}")
                
                # Vérifier si CUDA est disponible
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"📱 Utilisation du device: {device}")
                
                self.local_model = SentenceTransformer(
                    self.models[self.current_model],
                    device=device
                )
                
                logger.info("✅ Modèle local chargé avec succès")
                
                # Test rapide
                test_embedding = await self.encode_text("Test d'initialisation")
                logger.info(f"🧪 Test embedding: dimension {len(test_embedding)}")
                
            except Exception as e:
                logger.warning(f"⚠️ Échec du chargement local, basculement vers API: {e}")
                self.use_local = False
                
        if not self.use_local and not self.api_key:
            raise ValueError("Clé API Hugging Face requise si use_local=False")
    
    async def encode_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Encode un texte en vecteur d'embedding
        
        Args:
            text: Texte à encoder
            use_cache: Utiliser le cache pour éviter les recalculs
            
        Returns:
            Liste de floats représentant l'embedding
        """
        # Nettoyer le texte
        text = text.strip()
        if not text:
            return [0.0] * 384  # Dimension par défaut
        
        # Vérifier le cache
        cache_key = f"{self.current_model}:{hash(text)}"
        if use_cache and cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            if self.use_local and self.local_model:
                embedding = await self._encode_local(text)
            else:
                embedding = await self._encode_api(text)
            
            # Mettre en cache
            if use_cache:
                self.embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Erreur encodage text: {e}")
            # Retourner un embedding par défaut en cas d'erreur
            return [0.0] * 384
    
    async def _encode_local(self, text: str) -> List[float]:
        """Encode avec le modèle local"""
        loop = asyncio.get_event_loop()
        
        # Exécuter l'encodage dans un thread séparé pour éviter de bloquer
        def encode_sync():
            embedding = self.local_model.encode(text, convert_to_tensor=False)
            return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        
        embedding = await loop.run_in_executor(None, encode_sync)
        return embedding
    
    async def _encode_api(self, text: str) -> List[float]:
        """Encode via l'API Hugging Face"""
        url = f"{self.base_url}/{self.models[self.current_model]}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": text,
            "options": {
                "wait_for_model": True,
                "use_cache": True
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # L'API peut retourner différents formats
                    if isinstance(result, list):
                        if len(result) > 0 and isinstance(result[0], list):
                            return result[0]  # Premier embedding si batch
                        return result
                    elif isinstance(result, dict) and "embeddings" in result:
                        return result["embeddings"][0]
                    else:
                        raise ValueError(f"Format de réponse inattendu: {type(result)}")
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
    
    async def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode plusieurs textes en batch pour optimiser les performances
        
        Args:
            texts: Liste des textes à encoder
            batch_size: Taille des batches pour l'encodage
            
        Returns:
            Liste des embeddings correspondants
        """
        if not texts:
            return []
        
        embeddings = []
        
        # Traiter par batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            if self.use_local and self.local_model:
                batch_embeddings = await self._encode_batch_local(batch)
            else:
                # Pour l'API, traiter un par un (limitation API)
                batch_embeddings = []
                for text in batch:
                    emb = await self.encode_text(text, use_cache=True)
                    batch_embeddings.append(emb)
            
            embeddings.extend(batch_embeddings)
            
            # Petit délai pour éviter de surcharger
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return embeddings
    
    async def _encode_batch_local(self, texts: List[str]) -> List[List[float]]:
        """Encode un batch avec le modèle local"""
        loop = asyncio.get_event_loop()
        
        def encode_batch_sync():
            embeddings = self.local_model.encode(texts, convert_to_tensor=False)
            if len(embeddings.shape) == 1:
                return [embeddings.tolist()]
            return [emb.tolist() for emb in embeddings]
        
        embeddings = await loop.run_in_executor(None, encode_batch_sync)
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1: Premier embedding
            embedding2: Deuxième embedding
            
        Returns:
            Score de similarité entre -1 et 1
        """
        try:
            # Convertir en numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculer la similarité cosinus
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # S'assurer que le résultat est entre -1 et 1
            return float(np.clip(similarity, -1.0, 1.0))
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul similarité: {e}")
            return 0.0
    
    async def find_most_similar(self, query_embedding: List[float], 
                              candidate_embeddings: List[List[float]], 
                              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Trouve les embeddings les plus similaires à la requête
        
        Args:
            query_embedding: Embedding de la requête
            candidate_embeddings: Liste des embeddings candidats
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste des résultats triés par similarité décroissante
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.calculate_similarity(query_embedding, candidate)
            similarities.append({
                "index": i,
                "similarity": similarity
            })
        
        # Trier par similarité décroissante
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities[:top_k]
    
    async def switch_model(self, model_type: str):
        """
        Change le modèle d'embedding utilisé
        
        Args:
            model_type: Type de modèle ('multilingual', 'french', 'fast', 'legal')
        """
        if model_type not in self.models:
            raise ValueError(f"Modèle non supporté: {model_type}")
        
        old_model = self.current_model
        self.current_model = model_type
        
        # Vider le cache car le modèle a changé
        self.embedding_cache.clear()
        
        if self.use_local:
            try:
                logger.info(f"🔄 Changement de modèle: {old_model} -> {model_type}")
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.local_model = SentenceTransformer(
                    self.models[model_type],
                    device=device
                )
                
                logger.info(f"✅ Nouveau modèle chargé: {self.models[model_type]}")
                
            except Exception as e:
                logger.error(f"❌ Échec changement de modèle: {e}")
                # Revenir à l'ancien modèle
                self.current_model = old_model
                raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le modèle courant"""
        return {
            "current_model": self.current_model,
            "model_path": self.models[self.current_model],
            "use_local": self.use_local,
            "cache_size": len(self.embedding_cache),
            "available_models": list(self.models.keys()),
            "device": getattr(self.local_model, "device", "unknown") if self.local_model else "api"
        }
    
    async def clear_cache(self):
        """Vide le cache des embeddings"""
        cache_size = len(self.embedding_cache)
        self.embedding_cache.clear()
        logger.info(f"🗑️ Cache vidé: {cache_size} embeddings supprimés")
    
    async def precompute_embeddings(self, texts: List[str]) -> Dict[str, List[float]]:
        """
        Pré-calcule les embeddings pour une liste de textes
        Utile pour l'indexation initiale
        
        Args:
            texts: Liste des textes à pré-calculer
            
        Returns:
            Dictionnaire text -> embedding
        """
        logger.info(f"🔄 Pré-calcul de {len(texts)} embeddings...")
        
        embeddings = await self.encode_batch(texts)
        
        result = {}
        for text, embedding in zip(texts, embeddings):
            result[text] = embedding
        
        logger.info(f"✅ {len(result)} embeddings pré-calculés")
        return result