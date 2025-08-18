import os
from typing import Dict, Optional, List, Union
import logging
from dataclasses import dataclass

# Import conditionnel des services LLM
try:
    from .llm_service_gemini import GeminiLLMService, create_gemini_service
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Service Gemini non disponible - google-generativeai non installé")

# Import des autres services existants
try:
    from .llm_service_demo_phi4 import Phi4LLMService  # Votre service existant
    PHI4_AVAILABLE = True
except ImportError:
    PHI4_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration unifiée pour tous les services LLM"""
    provider: str = "gemini"  # gemini, phi4, openai, etc.
    model_name: str = "gemini-2.0-flash"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    
    # Paramètres spécifiques Gemini
    top_p: float = 0.95
    top_k: int = 64
    
    # Paramètres pour le contexte fiscal CGI
    system_prompt_type: str = "fiscal_cgi"  # fiscal_cgi, general, custom
    max_context_documents: int = 5
    use_conversation_history: bool = True

class UnifiedLLMService:
    """
    Service LLM unifié qui peut utiliser différents providers (Gemini, Phi4, etc.)
    Compatible avec l'architecture existante du projet RAG-CGI
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialise le service LLM unifié
        
        Args:
            config: Configuration LLM, utilise des valeurs par défaut si None
        """
        self.config = config or LLMConfig()
        self.active_service = None
        self.provider = self.config.provider.lower()
        
        # Initialisation du service selon le provider
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialise le service LLM selon le provider configuré"""
        
        if self.provider == "gemini" and GEMINI_AVAILABLE:
            self._initialize_gemini()
        elif self.provider == "phi4" and PHI4_AVAILABLE:
            self._initialize_phi4()
        else:
            self._fallback_to_available_service()
    
    def _initialize_gemini(self):
        """Initialise le service Gemini"""
        try:
            gemini_config = {
                'api_key': self.config.api_key or os.getenv('GOOGLE_API_KEY'),
                'model_name': self.config.model_name,
                'temperature': self.config.temperature,
                'max_output_tokens': self.config.max_tokens
            }
            
            self.active_service = create_gemini_service(gemini_config)
            logger.info(f"Service Gemini initialisé avec le modèle: {self.config.model_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Gemini: {e}")
            self._fallback_to_available_service()
    
    def _initialize_phi4(self):
        """Initialise le service Phi4 (votre service existant)"""
        try:
            # Adapter selon votre implémentation Phi4 existante
            self.active_service = Phi4LLMService(self.config)
            logger.info("Service Phi4 initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Phi4: {e}")
            self._fallback_to_available_service()
    
    def _fallback_to_available_service(self):
        """Fallback vers un service disponible"""
        if GEMINI_AVAILABLE and self.provider != "gemini":
            logger.info("Fallback vers Gemini")
            self.provider = "gemini"
            self._initialize_gemini()
        elif PHI4_AVAILABLE and self.provider != "phi4":
            logger.info("Fallback vers Phi4")
            self.provider = "phi4"
            self._initialize_phi4()
        else:
            raise RuntimeError("Aucun service LLM disponible")
    
    def generate_response(self, 
                         query: str, 
                         context_documents: Optional[List[Dict]] = None,
                         conversation_history: Optional[List[Dict]] = None,
                         **kwargs) -> str:
        """
        Génère une réponse - Interface unifiée pour tous les providers
        
        Args:
            query: Question de l'utilisateur
            context_documents: Documents RAG récupérés
            conversation_history: Historique de conversation
            **kwargs: Paramètres additionnels
            
        Returns:
            str: Réponse générée
        """
        if not self.active_service:
            raise RuntimeError("Aucun service LLM actif")
        
        try:
            # Adaptation selon le type de service
            if self.provider == "gemini":
                response = self.active_service.generate_response(
                    prompt=query,
                    context_documents=context_documents,
                    conversation_history=conversation_history
                )
                return response.content
            
            elif self.provider == "phi4":
                # Adapter selon votre interface Phi4 existante
                context = {
                    'documents': context_documents or [],
                    'history': conversation_history or []
                }
                return self.active_service.generate_response(query, context)
            
            else:
                raise ValueError(f"Provider non supporté: {self.provider}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return f"Erreur lors de la génération de la réponse: {str(e)}"
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Interface simplifiée pour chat - Compatible avec votre API existante
        
        Args:
            message: Message utilisateur
            context: Contexte (documents, historique)
            
        Returns:
            str: Réponse
        """
        if not context:
            context = {}
        
        return self.generate_response(
            query=message,
            context_documents=context.get('documents', []),
            conversation_history=context.get('history', [])
        )
    
    def switch_provider(self, provider: str, **config_updates) -> bool:
        """
        Change de provider LLM
        
        Args:
            provider: Nouveau provider (gemini, phi4, etc.)
            **config_updates: Mises à jour de configuration
            
        Returns:
            bool: True si le changement a réussi
        """
        try:
            # Mise à jour de la configuration
            old_provider = self.provider
            self.provider = provider.lower()
            
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # Réinitialisation du service
            self._initialize_service()
            
            logger.info(f"Provider changé de {old_provider} vers {self.provider}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du changement de provider: {e}")
            # Restaurer l'ancien provider
            self.provider = old_provider
            return False
    
    def get_available_providers(self) -> List[str]:
        """Retourne la liste des providers disponibles"""
        providers = []
        if GEMINI_AVAILABLE:
            providers.append("gemini")
        if PHI4_AVAILABLE:
            providers.append("phi4")
        return providers
    
    def get_status(self) -> Dict:
        """Retourne le statut du service"""
        return {
            "active_provider": self.provider,
            "available_providers": self.get_available_providers(),
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "service_healthy": self.active_service is not None
        }
    
    def health_check(self) -> Dict:
        """Vérifie la santé du service actif"""
        if not self.active_service:
            return {"status": "unhealthy", "error": "Aucun service actif"}
        
        if hasattr(self.active_service, 'health_check'):
            return self.active_service.health_check()
        else:
            # Test basique
            try:
                test_response = self.chat("Test")
                return {
                    "status": "healthy",
                    "provider": self.provider,
                    "test_successful": bool(test_response)
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "provider": self.provider,
                    "error": str(e)
                }

# Factory function pour créer le service unifié
def create_llm_service(provider: str = "gemini", **config_kwargs) -> UnifiedLLMService:
    """
    Factory pour créer le service LLM
    
    Args:
        provider: Provider à utiliser (gemini, phi4, etc.)
        **config_kwargs: Configuration additionnelle
        
    Returns:
        UnifiedLLMService: Service configuré
    """
    config = LLMConfig(provider=provider, **config_kwargs)
    return UnifiedLLMService(config)

# Configuration par défaut pour le projet CGI
CGI_GEMINI_CONFIG = LLMConfig(
    provider="gemini",
    model_name="gemini-2.0-flash",
    temperature=0.3,  # Température basse pour des réponses fiscales précises
    max_tokens=3000,
    system_prompt_type="fiscal_cgi",
    max_context_documents=5,
    use_conversation_history=True
)

# Fonction de compatibilité avec votre code existant
def get_llm_service() -> UnifiedLLMService:
    """
    Retourne une instance du service LLM configurée pour le CGI
    Fonction de compatibilité avec votre architecture existante
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logger.warning("GOOGLE_API_KEY non définie, utilisation du service par défaut")
    
    config = CGI_GEMINI_CONFIG
    config.api_key = api_key
    
    return UnifiedLLMService(config)

# Interface legacy pour maintenir la compatibilité
class LLMService:
    """
    Interface legacy pour maintenir la compatibilité avec votre code existant
    """
    
    def __init__(self):
        self.service = get_llm_service()
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Méthode compatible avec votre interface existante"""
        return self.service.chat(prompt, context)
    
    def chat(self, message: str, **kwargs) -> str:
        """Méthode de chat compatible"""
        return self.service.chat(message, kwargs.get('context'))

# Exemple d'utilisation
if __name__ == "__main__":
    # Test du service unifié
    service = create_llm_service(
        provider="gemini",
        api_key="AIzaSyB4uE7IqMpGhqDzNvGjDr1LXf5exgZDQso",
        model_name="gemini-2.0-flash",
        temperature=0.3
    )
    
    print("Statut:", service.get_status())
    print("Santé:", service.health_check())
    
    # Test avec contexte CGI
    context = {
        'documents': [
            {
                'content': 'La TVA au Bénin est fixée à 18% selon le CGI 2025',
                'source': 'CGI-2025.md',
                'score': 0.9
            }
        ]
    }
    
    response = service.chat("Quel est le taux de TVA ?", context)
    print("Réponse:", response)