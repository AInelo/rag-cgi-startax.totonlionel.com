import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Generator
from openai import OpenAI
import logging
from dataclasses import dataclass
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    MICROSOFT = "microsoft/phi-4:nebius"


@dataclass
class ConversationStats:
    total_tokens: int = 0
    response_times: List[float] = None
    successful_requests: int = 0
    failed_requests: int = 0

    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0

    @property
    def success_rate(self) -> float:
        total = self.successful_requests + self.failed_requests
        return (self.successful_requests / total * 100) if total > 0 else 0.0

class AdvancedHuggingFaceClient:
    """Client avancé pour Hugging Face avec fonctionnalités étendues"""

    def __init__(self, api_key: str, base_url: str = "https://router.huggingface.co/v1"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.stats = ConversationStats()
        self.system_prompt = None

    def set_system_prompt(self, prompt: str):
        """Définit un prompt système global"""
        self.system_prompt = prompt
        logger.info(f"Prompt système défini: {prompt[:50]}...")

    def clear_history(self):
        """Efface l'historique de conversation"""
        self.conversation_history.clear()
        logger.info("Historique de conversation effacé")

    def _prepare_messages(self, user_message: str, include_history: bool = True) -> List[Dict[str, str]]:
        """Prépare les messages pour l'API"""
        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        if include_history:
            messages.extend(self.conversation_history)

        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(self,
             message: str,
             model: ModelProvider = ModelProvider.MICROSOFT,
             temperature: float = 0.7,
             max_tokens: int = 1000,
             include_history: bool = True,
             stream: bool = False) -> Dict[str, Any]:
        """Envoie un message et retourne la réponse avec métadonnées"""

        start_time = time.time()
        messages = self._prepare_messages(message, include_history)

        try:
            logger.info(f"Envoi de la requête au modèle {model.value}")

            completion = self.client.chat.completions.create(
                model=model.value,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )

            response_time = time.time() - start_time
            self.stats.response_times.append(response_time)
            self.stats.successful_requests += 1

            if stream:
                return self._handle_stream_response(completion, message, response_time)
            else:
                return self._handle_standard_response(completion, message, response_time)

        except Exception as e:
            self.stats.failed_requests += 1
            logger.error(f"Erreur lors de la requête: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }

    def _handle_standard_response(self, completion, user_message: str, response_time: float) -> Dict[str, Any]:
        """Traite une réponse standard"""
        response_content = completion.choices[0].message.content

        # Ajouter à l'historique
        self.conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response_content}
        ])

        # Calculer les tokens (estimation)
        estimated_tokens = len(user_message.split()) + len(response_content.split())
        self.stats.total_tokens += estimated_tokens

        return {
            "success": True,
            "content": response_content,
            "response_time": response_time,
            "estimated_tokens": estimated_tokens,
            "finish_reason": completion.choices[0].finish_reason,
            "model_used": completion.model if hasattr(completion, 'model') else "unknown"
        }

    def _handle_stream_response(self, completion, user_message: str, start_time: float) -> Generator[Dict[str, Any], None, None]:
        """Traite une réponse en streaming"""
        full_content = ""

        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content

                yield {
                    "success": True,
                    "content": content,
                    "is_complete": False,
                    "accumulated_content": full_content
                }

        # Finaliser la réponse
        self.conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": full_content}
        ])

        response_time = time.time() - start_time
        estimated_tokens = len(user_message.split()) + len(full_content.split())
        self.stats.total_tokens += estimated_tokens

        yield {
            "success": True,
            "content": "",
            "is_complete": True,
            "accumulated_content": full_content,
            "response_time": response_time,
            "estimated_tokens": estimated_tokens
        }

    def batch_chat(self,
                   messages: List[str],
                   model: ModelProvider = ModelProvider.MICROSOFT,
                   max_workers: int = 3) -> List[Dict[str, Any]]:
        """Traite plusieurs messages en parallèle"""
        logger.info(f"Traitement en lot de {len(messages)} messages")

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_message = {
                executor.submit(self.chat, msg, model, include_history=False): msg
                for msg in messages
            }

            for future in as_completed(future_to_message):
                message = future_to_message[future]
                try:
                    result = future.result()
                    result["original_message"] = message
                    results.append(result)
                except Exception as e:
                    logger.error(f"Erreur pour le message '{message}': {e}")
                    results.append({
                        "success": False,
                        "error": str(e),
                        "original_message": message
                    })

        return results

    def compare_models(self, message: str, models: List[ModelProvider] = None) -> Dict[str, Dict[str, Any]]:
        """Compare la réponse de plusieurs modèles"""
        if models is None:
            models = list(ModelProvider)

        logger.info(f"Comparaison de {len(models)} modèles")
        results = {}

        for model in models:
            logger.info(f"Test du modèle {model.value}")
            result = self.chat(message, model=model, include_history=False)
            results[model.value] = result
            time.sleep(0.5)  # Petite pause entre les requêtes

        return results

    def conversation_loop(self, model: ModelProvider = ModelProvider.MICROSOFT):
        """Lance une boucle de conversation interactive"""
        print(f"\n🤖 Conversation avec {model.value}")
        print("Tapez 'quit' pour sortir, 'clear' pour effacer l'historique, 'stats' pour voir les statistiques\n")

        while True:
            try:
                user_input = input("Vous: ").strip()

                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'clear':
                    self.clear_history()
                    print("Historique effacé!\n")
                    continue
                elif user_input.lower() == 'stats':
                    self.print_stats()
                    continue
                elif not user_input:
                    continue

                print("Assistant: ", end="", flush=True)

                # Streaming response
                for chunk in self.chat(user_input, model=model, stream=True):
                    if not chunk["is_complete"]:
                        print(chunk["content"], end="", flush=True)

                print("\n")

            except KeyboardInterrupt:
                print("\n\nConversation interrompue.")
                break
            except Exception as e:
                print(f"\nErreur: {e}\n")

    def advanced_query(self,
                      message: str,
                      context: Optional[str] = None,
                      instructions: Optional[str] = None,
                      format_type: str = "text") -> Dict[str, Any]:
        """Requête avancée avec contexte et instructions spécifiques"""

        enhanced_message = message

        if context:
            enhanced_message = f"Contexte: {context}\n\nQuestion: {message}"

        if instructions:
            enhanced_message += f"\n\nInstructions: {instructions}"

        if format_type != "text":
            enhanced_message += f"\n\nFormat de réponse souhaité: {format_type}"

        return self.chat(enhanced_message)

    def print_stats(self):
        """Affiche les statistiques de performance"""
        print("\n📊 STATISTIQUES DE PERFORMANCE")
        print("=" * 40)
        print(f"Requêtes réussies: {self.stats.successful_requests}")
        print(f"Requêtes échouées: {self.stats.failed_requests}")
        print(f"Taux de réussite: {self.stats.success_rate:.1f}%")
        print(f"Temps de réponse moyen: {self.stats.avg_response_time:.2f}s")
        print(f"Total tokens estimés: {self.stats.total_tokens}")
        print(f"Messages dans l'historique: {len(self.conversation_history)}")
        print("=" * 40 + "\n")

    def export_conversation(self, filename: str = "conversation_export.json"):
        """Exporte la conversation vers un fichier JSON"""
        export_data = {
            "conversation_history": self.conversation_history,
            "stats": {
                "total_tokens": self.stats.total_tokens,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "avg_response_time": self.stats.avg_response_time
            },
            "system_prompt": self.system_prompt
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Conversation exportée vers {filename}")


# Fonction de démonstration avancée
def demo_advanced_features():
    """Démonstration des fonctionnalités avancées"""

    # Initialisation du client
    client = AdvancedHuggingFaceClient(api_key="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")

    # Définir un prompt système
    client.set_system_prompt(
        "Tu es un assistant IA expert et créatif. Réponds de manière détaillée et structurée. "
        "Utilise des exemples concrets et sois pédagogique."
    )

    print("🚀 DÉMONSTRATION DES FONCTIONNALITÉS AVANCÉES")
    print("=" * 50)

    # 1. Chat simple avec métadonnées
    print("\n1. Chat simple avec métadonnées:")
    result = client.chat("Explique-moi l'intelligence artificielle en 3 points clés")
    if result["success"]:
        print(f"Réponse: {result['content'][:100]}...")
        print(f"Temps de réponse: {result['response_time']:.2f}s")
        print(f"Tokens estimés: {result['estimated_tokens']}")

    # 2. Requête avancée avec contexte
    print("\n2. Requête avec contexte et instructions:")
    advanced_result = client.advanced_query(
        message="Comment optimiser ce processus?",
        context="Une entreprise de 50 employés veut automatiser sa gestion des stocks",
        instructions="Propose 5 solutions concrètes et chiffre les bénéfices potentiels",
        format_type="liste numérotée avec budgets"
    )
    if advanced_result["success"]:
        print(f"Réponse structurée: {advanced_result['content'][:150]}...")

    # 3. Traitement en lot
    print("\n3. Traitement en lot de plusieurs questions:")
    questions = [
        "Quelle est la capitale du Bénin?",
        "Comment faire du pain?",
        "Explique la blockchain en une phrase"
    ]
    batch_results = client.batch_chat(questions)
    for i, result in enumerate(batch_results):
        if result["success"]:
            print(f"Q{i+1}: {result['content'][:80]}...")

    # 4. Comparaison de modèles
    print("\n4. Comparaison de 2 modèles:")
    comparison = client.compare_models(
        "Écris un haiku sur la technologie",
        models=[ModelProvider.MICROSOFT, ModelProvider.META]
    )
    for model, result in comparison.items():
        if result["success"]:
            print(f"{model}: {result['content']}")
            print(f"Temps: {result['response_time']:.2f}s\n")

    # 5. Statistiques finales
    print("\n5. Statistiques de performance:")
    client.print_stats()

    # 6. Export de la conversation
    client.export_conversation("demo_conversation.json")
    print("Conversation exportée vers demo_conversation.json")

    return client


if __name__ == "__main__":
    # Lancer la démo
    client = demo_advanced_features()

    # Optionnel: lancer une conversation interactive
    choice = input("\n🗣️  Voulez-vous lancer une conversation interactive? (o/n): ")
    if choice.lower() in ['o', 'oui', 'y', 'yes']:
        client.conversation_loop()