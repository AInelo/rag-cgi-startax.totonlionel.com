# ==============================================================================
# FILE: app/database/vector_store.py - Base de données vectorielle avec ChromaDB
# ==============================================================================

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

import chromadb
from chromadb.config import Settings
import numpy as np

logger = logging.getLogger(__name__)

class VectorStore:
    """Base de données vectorielle pour stocker les documents CGI"""
    
    def __init__(self, 
                 persist_directory: str = "./vector_db",
                 collection_name: str = "cgi_documents"):
        """
        Initialize le vector store
        
        Args:
            persist_directory: Répertoire de persistance
            collection_name: Nom de la collection ChromaDB
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.is_initialized = False
        
        # Métadonnées de la collection
        self.collection_metadata = {
            "created_at": None,
            "last_updated": None,
            "document_count": 0,
            "total_tokens": 0
        }
    
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        if self.is_initialized:
            return
            
        try:
            # Créer le répertoire de persistance
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialiser le client ChromaDB
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Créer ou récupérer la collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name
                )
                logger.info(f"📚 Collection existante récupérée: {self.collection_name}")
                
                # Charger les métadonnées
                await self._load_metadata()
                
            except Exception:
                # Créer une nouvelle collection
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Documents du Code Général des Impôts",
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.info(f"📚 Nouvelle collection créée: {self.collection_name}")
                
                # Initialiser les métadonnées
                self.collection_metadata = {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "document_count": 0,
                    "total_tokens": 0
                }
                await self._save_metadata()
            
            self.is_initialized = True
            logger.info("✅ Vector store initialisé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation vector store: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]], 
                          embeddings: List[List[float]]):
        """
        Ajoute des documents avec leurs embeddings
        
        Args:
            documents: Liste des documents à ajouter
            embeddings: Embeddings correspondants
        """
        if not self.is_initialized:
            await self.initialize()
        
        if len(documents) != len(embeddings):
            raise ValueError("Le nombre de documents doit correspondre au nombre d'embeddings")
        
        try:
            # Préparer les données pour ChromaDB
            ids = []
            metadatas = []
            texts = []
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                # ID unique pour chaque document
                doc_id = doc.get('id', f"{uuid.uuid4()}")
                ids.append(doc_id)
                
                # Texte du document
                texts.append(doc['content'])
                
                # Métadonnées
                metadata = {
                    'title': doc.get('title', ''),
                    'section': doc.get('section', ''),
                    'article': doc.get('article', ''),
                    'source_file': doc.get('source_file', ''),
                    'chunk_index': doc.get('chunk_index', i),
                    'word_count': doc.get('word_count', 0),
                    'char_count': doc.get('char_count', 0),
                    'token_count': doc.get('token_count', 0),
                    'type': doc.get('type', 'content'),
                    'created_at': datetime.now().isoformat()
                }
                
                # Ajouter les métadonnées personnalisées s'il y en a
                if 'metadata' in doc:
                    metadata.update(doc['metadata'])
                
                metadatas.append(metadata)
            
            # Ajouter à la collection par batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                
                batch_ids = ids[i:end_idx]
                batch_texts = texts[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                batch_embeddings = embeddings[i:end_idx]
                
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                    embeddings=batch_embeddings
                )
                
                logger.info(f"📥 Batch {i//batch_size + 1} ajouté: {len(batch_ids)} documents")
            
            # Mettre à jour les métadonnées
            self.collection_metadata['document_count'] += len(documents)
            self.collection_metadata['total_tokens'] += sum(
                doc.get('token_count', 0) for doc in documents
            )
            self.collection_metadata['last_updated'] = datetime.now().isoformat()
            
            await self._save_metadata()
            
            logger.info(f"✅ {len(documents)} documents ajoutés à la collection")
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout documents: {e}")
            raise
    
    async def similarity_search(self, query_embedding: List[float], 
                              top_k: int = 5,
                              filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Recherche par similarité vectorielle
        
        Args:
            query_embedding: Embedding de la requête
            top_k: Nombre de résultats à retourner
            filter_criteria: Critères de filtrage optionnels
            
        Returns:
            Liste des documents les plus similaires
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Construire le filtre Where si spécifié
            where_clause = None
            if filter_criteria:
                where_clause = {}
                for key, value in filter_criteria.items():
                    if value is not None:
                        where_clause[key] = {"$eq": value}
            
            # Effectuer la recherche
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Traiter les résultats
            formatted_results = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    doc_id = results['ids'][0][i]
                    document = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Convertir la distance en score de similarité (0-1)
                    similarity_score = max(0, 1 - distance)
                    
                    result = {
                        'id': doc_id,
                        'content': document,
                        'similarity_score': round(similarity_score, 4),
                        'distance': round(distance, 4),
                        **metadata  # Ajouter toutes les métadonnées
                    }
                    
                    formatted_results.append(result)
            
            logger.info(f"🔍 Recherche terminée: {len(formatted_results)} résultats")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche similarité: {e}")
            return []
    
    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un document par son ID"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=['documents', 'metadatas']
            )
            
            if results['ids'] and len(results['ids']) > 0:
                return {
                    'id': results['ids'][0],
                    'content': results['documents'][0],
                    **results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération document {doc_id}: {e}")
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """Supprime un document par son ID"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            self.collection.delete(ids=[doc_id])
            
            # Mettre à jour les métadonnées
            self.collection_metadata['document_count'] = max(0, self.collection_metadata['document_count'] - 1)
            self.collection_metadata['last_updated'] = datetime.now().isoformat()
            await self._save_metadata()
            
            logger.info(f"🗑️ Document supprimé: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur suppression document {doc_id}: {e}")
            return False
    
    async def update_document(self, doc_id: str, new_content: str, 
                            new_embedding: List[float], 
                            new_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Met à jour un document existant"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # ChromaDB ne supporte pas la mise à jour directe
            # On supprime et on ajoute à nouveau
            await self.delete_document(doc_id)
            
            # Préparer les nouvelles données
            documents = [{
                'id': doc_id,
                'content': new_content,
                'metadata': new_metadata or {}
            }]
            
            await self.add_documents(documents, [new_embedding])
            
            logger.info(f"✏️ Document mis à jour: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour document {doc_id}: {e}")
            return False
    
    async def search_by_metadata(self, metadata_filter: Dict[str, Any], 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche par métadonnées uniquement"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            where_clause = {}
            for key, value in metadata_filter.items():
                if value is not None:
                    if isinstance(value, str):
                        where_clause[key] = {"$eq": value}
                    elif isinstance(value, list):
                        where_clause[key] = {"$in": value}
                    else:
                        where_clause[key] = {"$eq": value}
            
            results = self.collection.get(
                where=where_clause,
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    result = {
                        'id': results['ids'][i],
                        'content': results['documents'][i],
                        **results['metadatas'][i]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche par métadonnées: {e}")
            return []
    
    async def get_document_count(self) -> int:
        """Retourne le nombre de documents dans la collection"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"❌ Erreur comptage documents: {e}")
            return 0
    
    async def has_documents(self) -> bool:
        """Vérifie s'il y a des documents dans la collection"""
        count = await self.get_document_count()
        return count > 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la collection"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            count = await self.get_document_count()
            
            # Obtenir quelques échantillons pour les stats
            sample_results = self.collection.get(
                limit=10,
                include=['metadatas']
            )
            
            # Calculer des statistiques sur les métadonnées
            stats = {
                'total_documents': count,
                'collection_metadata': self.collection_metadata,
                'sample_metadata': sample_results.get('metadatas', [])[:3],
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
            
            # Statistiques par type si disponible
            if sample_results.get('metadatas'):
                types = {}
                sources = {}
                
                for metadata in sample_results['metadatas']:
                    doc_type = metadata.get('type', 'unknown')
                    source_file = metadata.get('source_file', 'unknown')
                    
                    types[doc_type] = types.get(doc_type, 0) + 1
                    sources[source_file] = sources.get(source_file, 0) + 1
                
                stats['document_types'] = types
                stats['source_files'] = sources
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération statistiques: {e}")
            return {
                'total_documents': 0,
                'error': str(e)
            }
    
    async def clear(self):
        """Vide complètement la collection"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Supprimer la collection
            self.client.delete_collection(name=self.collection_name)
            
            # Recréer une collection vide
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Documents du Code Général des Impôts",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # Réinitialiser les métadonnées
            self.collection_metadata = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "document_count": 0,
                "total_tokens": 0
            }
            
            await self._save_metadata()
            
            logger.info("🧹 Collection vidée avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur vidage collection: {e}")
            raise
    
    async def save_indexing_stats(self, stats: Dict[str, Any]):
        """Sauvegarde les statistiques d'indexation"""
        stats_file = os.path.join(self.persist_directory, "indexing_stats.json")
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
                
            logger.info(f"📊 Statistiques d'indexation sauvegardées: {stats_file}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur sauvegarde statistiques: {e}")
    
    async def _load_metadata(self):
        """Charge les métadonnées de la collection"""
        metadata_file = os.path.join(self.persist_directory, f"{self.collection_name}_metadata.json")
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.collection_metadata = json.load(f)
                logger.info("📋 Métadonnées de collection chargées")
            except Exception as e:
                logger.warning(f"⚠️ Erreur chargement métadonnées: {e}")
    
    async def _save_metadata(self):
        """Sauvegarde les métadonnées de la collection"""
        metadata_file = os.path.join(self.persist_directory, f"{self.collection_name}_metadata.json")
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.collection_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"⚠️ Erreur sauvegarde métadonnées: {e}")
    
    async def cleanup(self):
        """Nettoyage des ressources"""
        logger.info("🧹 Nettoyage du vector store...")
        
        # Sauvegarder les métadonnées finales
        if self.collection_metadata:
            await self._save_metadata()
        
        # ChromaDB gère automatiquement la persistance
        self.client = None
        self.collection = None
        self.is_initialized = False
        
        logger.info("✅ Nettoyage vector store terminé")