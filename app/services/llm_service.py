# ==============================================================================
# FILE: app/services/llm_service.py - Service LLM avec Fallback Hugging Face
# ==============================================================================

import asyncio
import logging
from enum import Enum
from typing import AsyncGenerator, Dict, Any, Optional, List
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    MICROSOFT = "microsoft/phi-4:nebius"
    META = "meta-llama/llama-3.1-8b-instruct"
    GOOGLE = "google/gemma-2-9b-it"
    MISTRAL = "mistralai/mistral-7b-instruct"
    QWEN = "qwen/qwen-2.5-7b-instruct"

class LLMService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"
        self.current_model = ModelProvider.MICROSOFT  # Modèle par défaut
        self.model_costs = {
            ModelProvider.MICROSOFT: 0.001,    # Coût estimé par 1k tokens
            ModelProvider.META: 0.0008,
            ModelProvider.GOOGLE: 0.0006,
            ModelProvider.MISTRAL: 0.0005,
            ModelProvider.QWEN: 0.0004         # Le moins cher
        }
        self.failed_models = set()  # Modèles qui ont échoué
        self.model_performance = {}  # Tracking des performances
        
    async def _get_next_available_model(self) -> Optional[ModelProvider]:
        """Récupère le prochain modèle disponible selon le coût"""
        available_models = [
            model for model in ModelProvider 
            if model not in self.failed_models
        ]
        
        if not available_models:
            # Reset si tous ont échoué
            self.failed_models.clear()
            available_models = list(ModelProvider)
        
        # Trier par coût (moins cher d'abord)
        available_models.sort(key=lambda m: self.model_costs[m])
        return available_models[0] if available_models else None
    
    async def _make_request(self, model: ModelProvider, messages: List[Dict], 
                          temperature: float = 0.3, max_tokens: int = 1000) -> Dict:
        """Fait une requête à un modèle spécifique"""
        url = f"{self.base_url}/{model.value}"
        
        # Format du prompt pour les modèles instruct
        prompt = self._format_messages_to_prompt(messages)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
                "do_sample": True,
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
    
    def _format_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Formate les messages en prompt pour les modèles instruct"""
        prompt_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"<|system|>\n{content}")
            elif role == "user":
                prompt_parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"<|assistant|>\n{content}")
        
        prompt_parts.append("<|assistant|>\n")  # Prompt pour la réponse
        return "\n".join(prompt_parts)
    
    async def generate_response_stream(self, messages: List[Dict], 
                                     temperature: float = 0.3,
                                     max_tokens: int = 1000) -> AsyncGenerator[Dict[str, Any], None]:
        """Génère une réponse en streaming avec fallback automatique"""
        
        model_attempts = 0
        max_attempts = len(ModelProvider)
        
        while model_attempts < max_attempts:
            current_model = await self._get_next_available_model()
            if not current_model:
                yield {
                    "type": "error",
                    "content": "Aucun modèle disponible",
                    "model": None
                }
                return
            
            try:
                logger.info(f"🤖 Tentative avec le modèle: {current_model.value}")
                
                yield {
                    "type": "model_switch",
                    "content": f"Utilisation du modèle: {current_model.value}",
                    "model": current_model.value,
                    "cost": self.model_costs[current_model]
                }
                
                # Pour simuler le streaming, on fait des requêtes par chunks
                start_time = datetime.now()
                
                response = await self._make_request(
                    current_model, messages, temperature, max_tokens
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Extraire le texte de la réponse
                if isinstance(response, list) and len(response) > 0:
                    generated_text = response[0].get("generated_text", "")
                elif isinstance(response, dict):
                    generated_text = response.get("generated_text", "")
                else:
                    generated_text = str(response)
                
                # Simuler le streaming en envoyant par chunks
                chunk_size = 50  # Caractères par chunk
                words = generated_text.split(" ")
                current_chunk = ""
                tokens_used = len(generated_text.split())
                
                for i, word in enumerate(words):
                    current_chunk += word + " "
                    
                    if len(current_chunk) >= chunk_size or i == len(words) - 1:
                        yield {
                            "type": "content",
                            "content": current_chunk,
                            "model": current_model.value,
                            "tokens": len(current_chunk.split()),
                            "partial": i < len(words) - 1
                        }
                        current_chunk = ""
                        
                        # Petit délai pour simuler le streaming
                        await asyncio.sleep(0.05)
                
                # Succès - enregistrer les performances
                self.model_performance[current_model] = {
                    "last_success": datetime.now(),
                    "processing_time": processing_time,
                    "tokens_generated": tokens_used
                }
                
                self.current_model = current_model
                
                yield {
                    "type": "complete",
                    "model": current_model.value,
                    "tokens_used": tokens_used,
                    "processing_time": processing_time,
                    "cost_estimate": self.model_costs[current_model] * (tokens_used / 1000)
                }
                
                return
                
            except Exception as e:
                logger.warning(f"❌ Modèle {current_model.value} a échoué: {str(e)}")
                self.failed_models.add(current_model)
                model_attempts += 1
                
                yield {
                    "type": "model_failed",
                    "content": f"Modèle {current_model.value} indisponible, basculement...",
                    "error": str(e),
                    "attempts_remaining": max_attempts - model_attempts
                }
                
                # Petit délai avant de réessayer
                await asyncio.sleep(1)
        
        # Tous les modèles ont échoué
        yield {
            "type": "error",
            "content": "Tous les modèles sont indisponibles actuellement",
            "failed_models": [m.value for m in self.failed_models]
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
            "current_model": self.current_model.value,
            "cost_per_1k_tokens": self.model_costs[self.current_model],
            "failed_models": [m.value for m in self.failed_models],
            "performance": {
                m.value: perf for m, perf in self.model_performance.items()
            }
        }
    
    async def reset_failed_models(self):
        """Reset la liste des modèles échoués (pour les tests)"""
        self.failed_models.clear()
        logger.info("🔄 Liste des modèles échoués réinitialisée")
    
    def get_cost_estimate(self, token_count: int, model: Optional[ModelProvider] = None) -> float:
        """Calcule le coût estimé pour un nombre de tokens"""
        target_model = model or self.current_model
        return self.model_costs[target_model] * (token_count / 1000)