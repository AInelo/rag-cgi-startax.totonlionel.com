# ==============================================================================
# FILE: app/services/reranker_service.py - Service de Re-ranking (DÉSACTIVÉ)
# ==============================================================================
# NOTE: Le re-ranking avec cross-encoder nécessite PyTorch qui est trop lourd
# Le système fonctionne sans re-ranking en utilisant uniquement la similarité cosinus
# qui est déjà très efficace pour la recherche vectorielle

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RerankerService:
    """
    Service de re-ranking - DÉSACTIVÉ pour économiser la mémoire
    Le système fonctionne sans re-ranking en utilisant uniquement la similarité cosinus
    qui est déjà très efficace pour la recherche vectorielle.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialise le service de re-ranking (désactivé)
        
        Args:
            model_name: Non utilisé (gardé pour compatibilité)
        """
        self.model = None
        self.is_initialized = False
        logger.info("ℹ️ Re-ranking désactivé (économie de mémoire - PyTorch non requis)")
    
    async def initialize(self):
        """Initialisation - re-ranking désactivé"""
        if self.is_initialized:
            return
        
        self.is_initialized = True
        logger.info("✅ Re-ranker initialisé (mode désactivé - pas de PyTorch requis)")
    
    async def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Re-ranking désactivé - retourne les documents tels quels (déjà triés par similarité cosinus)
        
        Args:
            query: Question/requête de l'utilisateur (non utilisé mais gardé pour compatibilité)
            documents: Liste de documents avec 'similarity_score' (déjà triés)
            top_k: Nombre de documents à retourner (None = tous)
            
        Returns:
            Documents tels quels (déjà triés par similarité cosinus)
        """
        if not documents:
            return []
        
        # Les documents sont déjà triés par similarité cosinus dans vector_store
        # On retourne simplement les top_k premiers
        logger.debug("ℹ️ Re-ranking désactivé, utilisation de la similarité cosinus uniquement")
        return documents[:top_k] if top_k else documents
    
    def is_available(self) -> bool:
        """Re-ranking non disponible (désactivé pour économiser la mémoire)"""
        return False
    
    async def cleanup(self):
        """Nettoie les ressources"""
        self.model = None
        self.is_initialized = False
        logger.info("🧹 Re-ranker nettoyé")

