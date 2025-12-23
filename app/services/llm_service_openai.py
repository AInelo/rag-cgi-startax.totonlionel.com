# ==============================================================================
# FILE: app/services/llm_service_openai.py - Service LLM OpenAI (Fallback)
# ==============================================================================

import os
import logging
from typing import List, Dict, Optional, AsyncGenerator, Any
from dataclasses import dataclass
import time
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI non disponible - openai non installé")

logger = logging.getLogger(__name__)

@dataclass
class OpenAIResponse:
    """Structure de réponse standardisée pour OpenAI"""
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    metadata: Optional[Dict] = None

class OpenAILLMService:
    """
    Service LLM utilisant OpenAI comme fallback pour Gemini
    Compatible avec l'interface GeminiLLMService
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "gpt-3.5-turbo",
                 temperature: float = 0.3,
                 max_output_tokens: int = 1000):
        """
        Initialise le service OpenAI
        
        Args:
            api_key: Clé API OpenAI
            model_name: Nom du modèle OpenAI à utiliser
            temperature: Température pour la génération
            max_output_tokens: Nombre maximum de tokens en sortie
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI n'est pas installé. Installez avec: pip install openai")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API OpenAI requise. Définissez OPENAI_API_KEY ou passez api_key")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        self.request_count = 0
        self.total_tokens = 0
        
        logger.info(f"✅ Service OpenAI initialisé: {model_name}")
    
    async def generate_response_stream(self, 
                                     prompt: str, 
                                     context_documents: Optional[List[Dict]] = None,
                                     conversation_history: Optional[List[Dict]] = None,
                                     system_prompt: Optional[str] = None,
                                     temperature: float = 0.3,
                                     max_tokens: int = 1000,
                                     personnalite: str = "expert_cgi") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Génère une réponse streamée en utilisant OpenAI
        Compatible avec l'interface Gemini
        """
        start_time = time.time()
        
        try:
            # Construire le prompt complet (même format que Gemini)
            full_prompt = self._build_cgi_prompt(
                user_query=prompt,
                context_documents=context_documents,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                personnalite=personnalite
            )
            
            logger.info(f"Génération streamée avec OpenAI {self.model_name} pour: {prompt[:100]}...")
            
            # Préparer les messages pour OpenAI
            messages = []
            
            # System prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system",
                    "content": self._get_default_system_prompt(personnalite)
                })
            
            # Contexte des documents
            if context_documents:
                context_text = "\n\n".join([
                    f"--- DOCUMENT {i+1} ---\n{doc.get('content', '')}"
                    for i, doc in enumerate(context_documents)
                ])
                messages.append({
                    "role": "system",
                    "content": f"Contexte du Code Général des Impôts du Bénin:\n\n{context_text}"
                })
            
            # Message utilisateur
            messages.append({"role": "user", "content": prompt})
            
            # Génération avec OpenAI en mode streaming
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            # Streamer la réponse
            response_content = ""
            chunk_count = 0
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_content += content
                    chunk_count += 1
                    yield {
                        "content": content,
                        "tokens": len(content.split()),  # Estimation
                        "complete": False
                    }
            
            # Finalisation
            response_time = time.time() - start_time
            self.request_count += 1
            
            yield {
                "content": "",
                "tokens": len(response_content.split()),
                "complete": True,
                "metadata": {
                    "model_used": self.model_name,
                    "response_time": response_time,
                    "total_content": response_content,
                    "chunks_received": chunk_count
                }
            }
            
            logger.info(f"✅ Réponse OpenAI générée en {response_time:.2f}s ({len(response_content)} caractères)")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération OpenAI: {e}")
            yield {
                "error": f"Erreur lors de la génération: {str(e)}",
                "complete": True,
                "quota_error": False
            }
    
    def _build_cgi_prompt(self, 
                         user_query: str,
                         context_documents: Optional[List[Dict]] = None,
                         conversation_history: Optional[List[Dict]] = None,
                         system_prompt: Optional[str] = None,
                         personnalite: str = "expert_cgi") -> str:
        """Construit le prompt pour OpenAI (similaire à Gemini)"""
        # Le prompt est construit dans generate_response_stream avec les messages
        # Cette méthode est gardée pour compatibilité
        return user_query
    
    def _get_default_system_prompt(self, personnalite: str) -> str:
        """Retourne le prompt système par défaut"""
        return """Tu es un assistant expert en fiscalité béninoise, spécialisé dans le Code Général des Impôts (CGI) du Bénin 2025.

EXPERTISE:
- Code Général des Impôts du Bénin 2025
- Régimes fiscaux (Réel, TPS)
- Calculs d'impôts et taxes (IS, IRCM, IRF, IBA, TVA, AIB, ITS, VPS, PATENTE, TPS)
- Réglementation fiscale béninoise
- Conseils fiscaux pratiques

INSTRUCTIONS:
- Réponds uniquement basé sur les documents du CGI fournis
- Cite les articles/sections pertinents quand possible
- Si l'information n'est pas dans les documents, indique-le clairement
- Donne des réponses précises et pratiques
- Utilise des exemples de calcul quand approprié
- Respecte la législation fiscale béninoise en vigueur"""
    
    def health_check(self) -> Dict:
        """Vérifie la santé du service OpenAI"""
        try:
            # Test simple
            test_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return {
                "status": "healthy",
                "model": self.model_name,
                "api_accessible": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "api_accessible": False,
                "error": str(e)
            }

def create_openai_service(config: Optional[Dict] = None) -> OpenAILLMService:
    """Factory function pour créer le service OpenAI"""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI n'est pas installé")
    
    config = config or {}
    return OpenAILLMService(
        api_key=config.get('api_key'),
        model_name=config.get('model_name', 'gpt-3.5-turbo'),
        temperature=config.get('temperature', 0.3),
        max_output_tokens=config.get('max_output_tokens', 1000)
    )

