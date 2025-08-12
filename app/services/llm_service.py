# ==============================================================================
# FILE: app/services/llm_service.py - Service LLM Microsoft Phi-4 via Hugging Face
# ==============================================================================

import asyncio
import logging
import os
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)

class ModelProvider:
    PHI4 = "microsoft/phi-4:nebius"  # Microsoft Phi-4 via Hugging Face

class LLMService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://router.huggingface.co/v1"
        self.current_model = ModelProvider.PHI4
        self.model_performance = {}
        
        # Initialiser le client OpenAI compatible Hugging Face
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
    async def _make_request(self, model: str, messages: List[Dict], 
                          temperature: float = 0.3, max_tokens: int = 1000) -> Dict:
        """Fait une requête à Microsoft Phi-4 via l'API Hugging Face"""
        try:
            logger.info(f"🤖 Appel à l'API Microsoft Phi-4: {model}")
            
            # Utiliser l'API OpenAI compatible
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Extraire la réponse
            response_content = completion.choices[0].message.content
            
            return {
                "choices": [{
                    "message": {
                        "content": response_content
                    }
                }],
                "model": completion.model if hasattr(completion, 'model') else model,
                "usage": {
                    "total_tokens": completion.usage.total_tokens if hasattr(completion.usage, 'total_tokens') else len(response_content.split())
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur API Microsoft Phi-4: {str(e)}")
            raise Exception(f"Erreur API: {str(e)}")
    
    async def generate_response_stream(self, messages: List[Dict], 
                                     temperature: float = 0.3,
                                     max_tokens: int = 1000) -> AsyncGenerator[Dict[str, Any], None]:
        """Génère une réponse en streaming avec Microsoft Phi-4"""
        
        try:
            logger.info(f"🤖 Génération de réponse avec Microsoft Phi-4")
            
            yield {
                "type": "model_switch",
                "content": f"Utilisation du modèle: {self.current_model}",
                "model": self.current_model
            }
            
            start_time = datetime.now()
            
            # Appel à l'API Microsoft Phi-4
            response = await self._make_request(
                self.current_model, messages, temperature, max_tokens
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extraire le texte de la réponse
            if isinstance(response, dict) and "choices" in response:
                generated_text = response["choices"][0]["message"]["content"]
                tokens_used = response.get("usage", {}).get("total_tokens", len(generated_text.split()))
            else:
                generated_text = str(response)
                tokens_used = len(generated_text.split())
            
            # Simuler le streaming en envoyant par chunks
            chunk_size = 50  # Caractères par chunk
            words = generated_text.split(" ")
            current_chunk = ""
            
            for i, word in enumerate(words):
                current_chunk += word + " "
                
                if len(current_chunk) >= chunk_size or i == len(words) - 1:
                    yield {
                        "type": "content",
                        "content": current_chunk,
                        "model": self.current_model,
                        "tokens": len(current_chunk.split()),
                        "partial": i < len(words) - 1
                    }
                    current_chunk = ""
                    
                    # Petit délai pour simuler le streaming
                    await asyncio.sleep(0.05)
            
            # Succès - enregistrer les performances
            self.model_performance[self.current_model] = {
                "last_success": datetime.now(),
                "processing_time": processing_time,
                "tokens_generated": tokens_used
            }
            
            yield {
                "type": "complete",
                "model": self.current_model,
                "tokens_used": tokens_used,
                "processing_time": processing_time
            }
                
        except Exception as e:
            logger.error(f"❌ Erreur avec Microsoft Phi-4: {str(e)}")
            yield {
                "type": "error",
                "content": f"Erreur lors de la génération: {str(e)}",
                "model": self.current_model
            }
    
    async def generate_single_response(self, messages: List[Dict], 
                                     temperature: float = 0.3,
                                     max_tokens: int = 1000) -> Dict[str, Any]:
        """Génère une réponse unique (non-streaming)"""
        full_response = ""
        metadata = {}
        
        async for chunk in self.generate_response_stream(messages, temperature, max_tokens):
            if chunk["type"] == "content":
                full_response += chunk["content"]
            elif chunk["type"] == "complete":
                metadata = chunk
            elif chunk["type"] == "error":
                return {
                    "success": False,
                    "content": "",
                    "error": chunk["content"],
                    "metadata": {}
                }
        
        return {
            "success": True,
            "content": full_response.strip(),
            "error": None,
            "metadata": metadata
        }
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """Retourne les informations du modèle courant"""
        return {
            "current_model": self.current_model,
            "api_provider": "Hugging Face Router",
            "base_url": self.base_url,
            "performance": {
                self.current_model: perf for perf in self.model_performance.values()
            }
        }
    
    async def cleanup(self):
        """Nettoyage des ressources"""
        try:
            if hasattr(self, 'client'):
                # Le client OpenAI n'a pas de méthode close() explicite
                pass
            logger.info("🧹 Service LLM nettoyé")
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage LLM: {e}")