# ==============================================================================
# FILE: app/database/vector_store.py - Base de données vectorielle ultra-légère avec scikit-learn
# ==============================================================================

import asyncio
import logging
import json
import os
import pickle
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class VectorStore:
    """Base de données vectorielle ultra-légère pour stocker les documents CGI"""
    
    def __init__(self, 
                 persist_directory: str = "./vector_db",
                 collection_name: str = "cgi_documents"):
        """
        Initialize le vector store ultra-léger
        
        Args:
            persist_directory: Répertoire de persistance
            collection_name: Nom de la collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.is_initialized = False
        
        # Stockage en mémoire (plus rapide)
        self.documents = {}  # id -> document
        self.embeddings = []  # Liste des embeddings
        self.document_ids = []  # Liste des IDs dans l'ordre
        
        # Métadonnées de la collection
        self.collection_metadata = {
            "created_at": None,
            "last_updated": None,
            "document_count": 0,
            "total_tokens": 0
        }
    
    async def initialize(self):
        """Initialize le vector store ultra-léger"""
        if self.is_initialized:
            return
            
        try:
            # Créer le répertoire de persistance
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Charger les données existantes si elles existent
            await self._load_data()
            
            if not self.documents:
                # Initialiser les métadonnées pour une nouvelle collection
                self.collection_metadata = {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "document_count": 0,
                    "total_tokens": 0
                }
                await self._save_data()
            
            self.is_initialized = True
            logger.info("✅ Vector store ultra-léger initialisé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation vector store: {e}")
            raise
    
    async def add_documents(self, 
                           documents: List[Dict[str, Any]], 
                          embeddings: List[List[float]]):
        """
        Ajoute des documents avec leurs embeddings
        
        Args:
            documents: Liste des documents à ajouter
            embeddings: Liste des embeddings correspondants
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            for doc, embedding in zip(documents, embeddings):
                # Générer un ID unique
                doc_id = str(uuid.uuid4())
                
                # Stocker le document
                self.documents[doc_id] = {
                    "id": doc_id,
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {}),
                    "created_at": datetime.now().isoformat()
                }
                
                # Stocker l'embedding
                self.embeddings.append(embedding)
                self.document_ids.append(doc_id)
            
            # Mettre à jour les métadonnées
            self.collection_metadata["document_count"] = len(self.documents)
            self.collection_metadata["last_updated"] = datetime.now().isoformat()
            
            # Sauvegarder
            await self._save_data()
            
            logger.info(f"✅ {len(documents)} documents ajoutés au vector store")
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout documents: {e}")
            raise
    
    async def similarity_search(self, query_embedding: List[float], 
                              top_k: int = 5,
                              filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Recherche de similarité avec l'embedding de la requête
        
        Args:
            query_embedding: Embedding de la requête
            top_k: Nombre de résultats à retourner
            filter_criteria: Critères de filtrage (optionnel)
            
        Returns:
            Liste des documents les plus similaires
        """
        if not self.is_initialized or not self.embeddings:
            return []
        
        try:
            # Convertir en arrays numpy
            query_array = np.array(query_embedding).reshape(1, -1)
            embeddings_array = np.array(self.embeddings)
            
            # Calculer les similarités cosinus
            similarities = cosine_similarity(query_array, embeddings_array)[0]
            
            # Créer la liste des résultats avec scores
            results = []
            for i, similarity in enumerate(similarities):
                doc_id = self.document_ids[i]
                document = self.documents[doc_id]
                
                # Appliquer les filtres si spécifiés
                if filter_criteria and not self._matches_filter(document, filter_criteria):
                    continue
                
                results.append({
                    "id": doc_id,
                    "content": document["content"],
                    "metadata": document["metadata"],
                    "similarity_score": float(similarity),
                    "created_at": document["created_at"]
                })
            
            # Trier par score de similarité décroissant
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Retourner les top_k résultats
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche similarité: {e}")
            return []
    
    def _matches_filter(self, document: Dict[str, Any], filter_criteria: Dict[str, Any]) -> bool:
        """Vérifie si un document correspond aux critères de filtrage avancé"""
        try:
            metadata = document.get("metadata", {})
            
            for key, value in filter_criteria.items():
                # Filtrage par type d'impôt
                if key == "impot_type":
                    impot_types = metadata.get("impot_types", [])
                    if value.upper() not in [it.upper() for it in impot_types]:
                        return False
                
                # Filtrage par régime
                elif key == "regime":
                    regime = metadata.get("regime", "")
                    if regime.upper() != value.upper():
                        return False
                
                # Filtrage par année de mise à jour
                elif key == "update_year":
                    update_date = metadata.get("update_date", "")
                    if not update_date or str(value) not in update_date:
                        return False
                
                # Filtrage par catégorie fiscale
                elif key == "fiscal_category":
                    fiscal_category = metadata.get("fiscal_category", "")
                    if fiscal_category.upper() != value.upper():
                        return False
                
                # Filtrage standard (métadonnées directes)
                elif key in metadata:
                    if metadata[key] != value:
                        return False
                else:
                    # Si la clé n'existe pas dans les métadonnées, le filtre échoue
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ Erreur filtrage: {e}")
            return False
    
    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un document par son ID"""
        if not self.is_initialized:
            return None
            
        return self.documents.get(doc_id)
    
    async def delete_document(self, doc_id: str) -> bool:
        """Supprime un document"""
        if not self.is_initialized or doc_id not in self.documents:
            return False
    
        try:
            # Trouver l'index de l'embedding
            if doc_id in self.document_ids:
                idx = self.document_ids.index(doc_id)
                self.embeddings.pop(idx)
                self.document_ids.pop(idx)
            
            # Supprimer le document
            del self.documents[doc_id]
            
            # Mettre à jour les métadonnées
            self.collection_metadata["document_count"] = len(self.documents)
            self.collection_metadata["last_updated"] = datetime.now().isoformat()
            
            await self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur suppression document: {e}")
            return False
    
    async def get_document_count(self) -> int:
        """Retourne le nombre de documents"""
        return len(self.documents) if self.is_initialized else 0
    
    async def has_documents(self) -> bool:
        """Vérifie s'il y a des documents"""
        return len(self.documents) > 0 if self.is_initialized else False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du vector store"""
        if not self.is_initialized:
            return {}
        
        return {
            "collection_name": self.collection_name,
            "document_count": len(self.documents),
            "embedding_count": len(self.embeddings),
            "embedding_dimension": len(self.embeddings[0]) if self.embeddings else 0,
            "metadata": self.collection_metadata,
            "storage_size_mb": await self._get_storage_size()
        }
    
    async def _get_storage_size(self) -> float:
        """Calcule la taille de stockage en MB"""
        try:
            total_size = 0
            for doc in self.documents.values():
                total_size += len(str(doc))
            for emb in self.embeddings:
                total_size += len(emb) * 8  # 8 bytes par float64
            
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    async def clear(self):
        """Vide complètement le vector store"""
        if not self.is_initialized:
            return
        
        try:
            self.documents.clear()
            self.embeddings.clear()
            self.document_ids.clear()
            
            # Réinitialiser les métadonnées
            self.collection_metadata = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "document_count": 0,
                "total_tokens": 0
            }
            
            await self._save_data()
            logger.info("🗑️ Vector store vidé")
            
        except Exception as e:
            logger.error(f"❌ Erreur vidage vector store: {e}")
    
    async def _save_data(self):
        """Sauvegarde les données sur disque"""
        try:
            data = {
                "documents": self.documents,
                "embeddings": self.embeddings,
                "document_ids": self.document_ids,
                "metadata": self.collection_metadata
            }
            
            filepath = os.path.join(self.persist_directory, f"{self.collection_name}.pkl")
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde données: {e}")
    
    async def _load_data(self):
        """Charge les données depuis le disque"""
        try:
            filepath = os.path.join(self.persist_directory, f"{self.collection_name}.pkl")
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    data = pickle.load(f)
                
                self.documents = data.get("documents", {})
                self.embeddings = data.get("embeddings", [])
                self.document_ids = data.get("document_ids", [])
                self.collection_metadata = data.get("metadata", self.collection_metadata)
                
                logger.info(f"📚 Données chargées: {len(self.documents)} documents")
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible de charger les données existantes: {e}")
            # Initialiser avec des valeurs par défaut
            self.documents = {}
            self.embeddings = []
            self.document_ids = []
    
    async def save_indexing_stats(self, stats: Dict[str, Any]):
        """Sauvegarde les statistiques d'indexation (compatibilité)"""
        try:
            # Mettre à jour les métadonnées avec les stats
            if "total_chunks" in stats:
                self.collection_metadata["total_tokens"] = stats.get("total_chunks", 0)
            
            await self._save_data()
            logger.info("📊 Statistiques d'indexation sauvegardées")
        except Exception as e:
            logger.warning(f"⚠️ Erreur sauvegarde statistiques: {e}")
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            await self._save_data()
            logger.info("🧹 Vector store nettoyé")
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage: {e}")