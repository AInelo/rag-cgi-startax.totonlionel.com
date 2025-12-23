import google.generativeai as genai
import os
import logging
from typing import List, Dict, Optional, Union, AsyncGenerator, Any
from dataclasses import dataclass
import json
import time
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GeminiResponse:
    """Structure de réponse standardisée pour Gemini"""
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    metadata: Optional[Dict] = None

class GeminiLLMService:
    """
    Service LLM utilisant Google Gemini pour le projet RAG-CGI
    Compatible avec la structure existante du projet
    """
    
    # Modèles Gemini gratuits disponibles
    FREE_MODELS = [
        "gemini-2.0-flash",      # Gratuit
        "gemini-1.5-flash",      # Gratuit
        "gemini-1.5-flash-8b",   # Gratuit
        "gemini-1.5-pro",        # Gratuit
        "gemma-3",               # Gratuit
        "gemma-3n"               # Gratuit
    ]
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "gemini-2.0-flash",
                 temperature: float = 0.7,
                 max_output_tokens: int = 2048):
        """
        Initialise le service Gemini
        
        Args:
            api_key: Clé API Google AI Studio
            model_name: Nom du modèle Gemini à utiliser
            temperature: Température pour la génération (0.0 à 1.0)
            max_output_tokens: Nombre maximum de tokens en sortie
        """
        # Configuration de l'API
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API Google AI Studio requise. Définissez GOOGLE_API_KEY ou passez api_key")
        
        genai.configure(api_key=self.api_key)
        
        # Vérifier que le modèle est gratuit
        if model_name not in self.FREE_MODELS:
            logger.warning(f"Modèle {model_name} n'est pas dans la liste des modèles gratuits. Utilisation de gemini-2.0-flash")
            model_name = "gemini-2.0-flash"
        
        # Configuration du modèle
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        # Configuration de génération
        self.generation_config = {
            "temperature": self.temperature,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": self.max_output_tokens,
        }
        
        # Initialisation du modèle
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config
            )
            logger.info(f"Service Gemini initialisé avec le modèle: {self.model_name}")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Gemini: {e}")
            raise
        
        # Statistiques
        self.request_count = 0
        self.total_tokens = 0
        
    async def generate_response_stream(self, 
                                     prompt: str, 
                                     context_documents: Optional[List[Dict]] = None,
                                     conversation_history: Optional[List[Dict]] = None,
                                     system_prompt: Optional[str] = None,
                                     temperature: float = 0.3,
                                     max_tokens: int = 1000,
                                     personnalite: str = "expert_cgi") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Génère une réponse streamée en utilisant Gemini avec contexte RAG
        
        Args:
            prompt: Question/requête de l'utilisateur
            context_documents: Documents récupérés par le système RAG
            conversation_history: Historique de la conversation
            system_prompt: Prompt système personnalisé
            temperature: Température pour la génération
            max_tokens: Nombre maximum de tokens
            
        Yields:
            Chunks de réponse avec métadonnées
        """
        start_time = time.time()
        
        try:
            # Construction du prompt complet pour le contexte fiscal CGI
            full_prompt = self._build_cgi_prompt(
                user_query=prompt,
                context_documents=context_documents,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                personnalite=personnalite
            )
            
            # Génération avec Gemini en mode streaming
            logger.info(f"Génération streamée avec {self.model_name} pour: {prompt[:100]}...")
            logger.debug(f"Longueur du prompt complet: {len(full_prompt)} caractères")
            
            # Utiliser le mode streaming de Gemini
            try:
                response = self.model.generate_content(
                    full_prompt,
                    stream=True,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens
                    }
                )
                logger.debug("✅ Réponse Gemini obtenue, début du streaming...")
            except Exception as gen_error:
                logger.error(f"❌ Erreur lors de l'appel à Gemini: {gen_error}")
                raise
            
            # Streamer la réponse
            response_content = ""
            chunk_count = 0
            
            for chunk in response:
                try:
                    # Gérer différentes structures de chunks Gemini
                    text_content = None
                    
                    # Essayer d'abord chunk.text (méthode directe)
                    if hasattr(chunk, 'text') and chunk.text:
                        text_content = chunk.text
                    # Sinon essayer chunk.parts[0].text
                    elif hasattr(chunk, 'parts') and chunk.parts and len(chunk.parts) > 0:
                        if hasattr(chunk.parts[0], 'text') and chunk.parts[0].text:
                            text_content = chunk.parts[0].text
                    
                    if text_content:
                        response_content += text_content
                        chunk_count += 1
                        yield {
                            "content": text_content,
                            "tokens": len(text_content.split()),  # Estimation
                            "complete": False
                        }
                except Exception as chunk_error:
                    logger.warning(f"⚠️ Erreur traitement chunk: {chunk_error}")
                    continue
            
            # Finalisation
            response_time = time.time() - start_time
            self.request_count += 1
            
            # Si aucune réponse n'a été générée, vérifier pourquoi
            if not response_content:
                logger.warning(f"⚠️ Aucun contenu généré. Chunks reçus: {chunk_count}")
                # Essayer de récupérer la réponse complète si disponible
                try:
                    if hasattr(response, 'text') and response.text:
                        response_content = response.text
                        logger.info("✅ Contenu récupéré depuis response.text")
                except:
                    pass
            
            yield {
                "content": "",
                "tokens": len(response_content.split()) if response_content else 0,
                "complete": True,
                "metadata": {
                    "model_used": self.model_name,
                    "response_time": response_time,
                    "total_content": response_content,
                    "chunks_received": chunk_count
                }
            }
            
            if response_content:
                logger.info(f"✅ Réponse streamée générée en {response_time:.2f}s ({len(response_content)} caractères, {chunk_count} chunks)")
            else:
                logger.error(f"❌ Aucune réponse générée après {response_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération streamée: {e}")
            yield {
                "error": f"Erreur lors de la génération: {str(e)}",
                "complete": True
            }
    
    def generate_response(self, 
                         prompt: str, 
                         context_documents: Optional[List[Dict]] = None,
                         conversation_history: Optional[List[Dict]] = None,
                         system_prompt: Optional[str] = None,
                         personnalite: str = "expert_cgi") -> GeminiResponse:
        """
        Génère une réponse en utilisant Gemini avec contexte RAG
        
        Args:
            prompt: Question/requête de l'utilisateur
            context_documents: Documents récupérés par le système RAG
            conversation_history: Historique de la conversation
            system_prompt: Prompt système personnalisé
            
        Returns:
            GeminiResponse: Réponse formatée avec métadonnées
        """
        start_time = time.time()
        
        try:
            # Construction du prompt complet pour le contexte fiscal CGI
            full_prompt = self._build_cgi_prompt(
                user_query=prompt,
                context_documents=context_documents,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                personnalite="expert_cgi"  # Par défaut pour la méthode non-streamée
            )
            
            # Génération avec Gemini
            logger.info(f"Génération avec {self.model_name} pour: {prompt[:100]}...")
            response = self.model.generate_content(full_prompt)
            
            # Calcul du temps de réponse
            response_time = time.time() - start_time
            
            # Mise à jour des statistiques
            self.request_count += 1
            
            # Construction de la réponse
            gemini_response = GeminiResponse(
                content=response.text,
                model_used=self.model_name,
                response_time=response_time,
                metadata={
                    "request_id": self.request_count,
                    "timestamp": datetime.now().isoformat(),
                    "context_docs_count": len(context_documents) if context_documents else 0,
                    "has_history": bool(conversation_history)
                }
            )
            
            logger.info(f"Réponse générée en {response_time:.2f}s")
            return gemini_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return GeminiResponse(
                content=f"Erreur lors de la génération de la réponse: {str(e)}",
                model_used=self.model_name,
                response_time=time.time() - start_time,
                metadata={"error": True, "error_message": str(e)}
            )
    
    def _build_cgi_prompt(self, 
                         user_query: str,
                         context_documents: Optional[List[Dict]] = None,
                         conversation_history: Optional[List[Dict]] = None,
                         system_prompt: Optional[str] = None,
                         personnalite: str = "expert_cgi") -> str:
        """
        Construit le prompt spécialisé pour les questions fiscales CGI du Bénin
        avec support des personnalités
        """
        
        # Import du service de personnalités
        try:
            from app.services.personnalite_service import PersonnaliteService
            personnalite_service = PersonnaliteService()
            default_system_prompt = personnalite_service.get_prompt_system(personnalite)
        except ImportError:
            # Fallback si le service n'est pas disponible
            default_system_prompt = """Tu es un assistant expert en fiscalité béninoise, spécialisé dans le Code Général des Impôts (CGI) du Bénin 2025.

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

        # Utilisation du prompt système fourni ou par défaut
        system_section = system_prompt or default_system_prompt
        
        # Construction du contexte documentaire
        context_section = ""
        if context_documents:
            context_section = "\n\nDOCUMENTS DE RÉFÉRENCE CGI:\n"
            for i, doc in enumerate(context_documents, 1):
                source = doc.get('source', 'Document inconnu')
                content = doc.get('content', doc.get('text', ''))
                score = doc.get('score', 0)
                
                context_section += f"\n--- Document {i} (source: {source}, pertinence: {score:.2f}) ---\n{content}\n"
        
        # Construction de l'historique
        history_section = ""
        if conversation_history:
            history_section = "\n\nHISTORIQUE DE LA CONVERSATION:\n"
            # Prendre les 3 derniers échanges pour éviter un contexte trop long
            recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
            
            for exchange in recent_history:
                user_msg = exchange.get('user', exchange.get('human', ''))
                assistant_msg = exchange.get('assistant', exchange.get('ai', ''))
                history_section += f"Utilisateur: {user_msg}\nAssistant: {assistant_msg}\n\n"
        
        # Construction du prompt final
        full_prompt = f"""{system_section}

{context_section}

{history_section}

QUESTION ACTUELLE:
{user_query}

RÉPONSE (basée uniquement sur les documents CGI fournis):"""
        
        return full_prompt
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Interface simplifiée pour chat - compatible avec l'API existante
        
        Args:
            message: Message de l'utilisateur
            context: Contexte optionnel (documents, historique, etc.)
            
        Returns:
            str: Réponse de l'assistant
        """
        context_docs = context.get('documents', []) if context else []
        history = context.get('history', []) if context else []
        
        response = self.generate_response(
            prompt=message,
            context_documents=context_docs,
            conversation_history=history
        )
        
        return response.content
    
    def get_available_models(self) -> List[str]:
        """
        Retourne la liste des modèles Gemini gratuits disponibles
        """
        return self.FREE_MODELS.copy()
    
    def switch_model(self, model_name: str) -> bool:
        """
        Change de modèle Gemini (uniquement vers les modèles gratuits)
        
        Args:
            model_name: Nom du nouveau modèle
            
        Returns:
            bool: True si le changement a réussi
        """
        if model_name not in self.FREE_MODELS:
            logger.error(f"Modèle {model_name} n'est pas gratuit. Modèles gratuits: {self.FREE_MODELS}")
            return False
            
        try:
            # Test du nouveau modèle
            test_model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=self.generation_config
            )
            
            # Si le test réussit, mise à jour
            self.model = test_model
            self.model_name = model_name
            logger.info(f"Modèle changé vers: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du changement de modèle: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        Retourne les statistiques d'utilisation
        """
        return {
            "model_name": self.model_name,
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "free_models_available": self.FREE_MODELS
        }
    
    def health_check(self) -> Dict:
        """
        Vérifie la santé du service
        """
        try:
            # Test simple
            test_response = self.model.generate_content("Test de connectivité")
            return {
                "status": "healthy",
                "model": self.model_name,
                "api_accessible": True,
                "test_response_length": len(test_response.text),
                "is_free_model": self.model_name in self.FREE_MODELS
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "api_accessible": False,
                "error": str(e)
            }

# Fonction factory pour créer le service (compatibilité avec l'architecture existante)
def create_gemini_service(config: Optional[Dict] = None) -> GeminiLLMService:
    """
    Factory function pour créer une instance du service Gemini
    
    Args:
        config: Configuration optionnelle
        
    Returns:
        GeminiLLMService: Instance configurée
    """
    if config is None:
        config = {}
    
    return GeminiLLMService(
        api_key=config.get('api_key'),
        model_name=config.get('model_name', 'gemini-2.0-flash'),
        temperature=config.get('temperature', 0.7),
        max_output_tokens=config.get('max_output_tokens', 2048)
    )

# Interface de compatibilité avec l'API existante
class LLMService:
    """
    Wrapper pour maintenir la compatibilité avec l'interface existante
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.gemini_service = create_gemini_service(config)
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Interface compatible avec le service existant"""
        return self.gemini_service.chat(prompt, context)
    
    def chat(self, message: str, **kwargs) -> str:
        """Interface compatible pour chat"""
        return self.gemini_service.chat(message, kwargs.get('context'))
    
    async def generate_response_stream(self, 
                                     messages: List[Dict[str, str]], 
                                     temperature: float = 0.3,
                                     max_tokens: int = 1000) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Interface compatible pour le streaming - extrait la question des messages
        """
        # Extraire la question du dernier message utilisateur
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            yield {"error": "Aucun message utilisateur trouvé", "complete": True}
            return
        
        # Appeler le service Gemini en streaming
        async for chunk in self.gemini_service.generate_response_stream(
            prompt=user_message,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk
    
    def get_current_model_info(self) -> Dict:
        """Interface compatible pour obtenir les infos du modèle"""
        return self.gemini_service.get_stats()

# Exemple d'utilisation dans votre projet
if __name__ == "__main__":
    # Test du service
    config = {
        'api_key': os.getenv('GOOGLE_API_KEY'),  # Utilise la variable d'environnement
        'model_name': 'gemini-2.0-flash',
        'temperature': 0.3  # Température basse pour des réponses fiscales précises
    }
    
    service = create_gemini_service(config)
    
    # Test de santé
    health = service.health_check()
    print("État du service:", health)
    
    # Test avec contexte fiscal
    test_context = {
        'documents': [
            {
                'content': 'Article 123: Le taux de TVA standard au Bénin est de 18%',
                'source': 'CGI-2025-TVA.md',
                'score': 0.95
            }
        ]
    }
    
    response = service.chat(
        "Quel est le taux de TVA au Bénin ?", 
        context=test_context
    )
    print("Réponse:", response)