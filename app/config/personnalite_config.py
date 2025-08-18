# ==============================================================================
# FILE: app/config/personnalite_config.py - Configuration des Personnalités
# ==============================================================================

import os
from typing import Dict, Any

class PersonnaliteConfig:
    """
    Configuration des paramètres pour chaque personnalité du chatbot
    """
    
    # Configuration par défaut des personnalités
    DEFAULT_CONFIG = {
        "expert": {
            "temperature": 0.1,        # Réponses déterministes et cohérentes
            "max_tokens": 150,         # Réponses courtes
            "top_p": 0.9,             # Focus sur les réponses les plus probables
            "top_k": 40,              # Limiter les choix
            "description": "Réponses courtes et directes"
        },
        "expert_cgi": {
            "temperature": 0.3,        # Équilibré entre créativité et précision
            "max_tokens": 1000,        # Réponses détaillées
            "top_p": 0.95,            # Plus de variété dans les explications
            "top_k": 64,              # Plus de choix pour la diversité
            "description": "Réponses détaillées avec références complètes"
        },
        "mathematicien": {
            "temperature": 0.2,        # Précision mathématique
            "max_tokens": 800,         # Réponses techniques
            "top_p": 0.92,            # Focus sur la précision
            "top_k": 50,              # Choix équilibrés
            "description": "Formules mathématiques et calculs précis"
        }
    }
    
    def __init__(self):
        """Initialise la configuration avec les valeurs par défaut ou d'environnement"""
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Charge la configuration depuis les variables d'environnement ou utilise les valeurs par défaut
        """
        config = self.DEFAULT_CONFIG.copy()
        
        # Permettre la surcharge via variables d'environnement
        for personnalite in config.keys():
            # Température
            temp_key = f"{personnalite.upper()}_TEMPERATURE"
            if temp_key in os.environ:
                try:
                    config[personnalite]["temperature"] = float(os.environ[temp_key])
                except ValueError:
                    pass
            
            # Max tokens
            tokens_key = f"{personnalite.upper()}_MAX_TOKENS"
            if tokens_key in os.environ:
                try:
                    config[personnalite]["max_tokens"] = int(os.environ[tokens_key])
                except ValueError:
                    pass
        
        return config
    
    def get_config(self, personnalite: str) -> Dict[str, Any]:
        """
        Récupère la configuration pour une personnalité donnée
        
        Args:
            personnalite: Nom de la personnalité
            
        Returns:
            Configuration de la personnalité
        """
        return self.config.get(personnalite, self.config["expert_cgi"])
    
    def get_temperature(self, personnalite: str) -> float:
        """Récupère la température pour une personnalité"""
        return self.get_config(personnalite)["temperature"]
    
    def get_max_tokens(self, personnalite: str) -> int:
        """Récupère le nombre max de tokens pour une personnalité"""
        return self.get_config(personnalite)["max_tokens"]
    
    def get_top_p(self, personnalite: str) -> float:
        """Récupère le top_p pour une personnalité"""
        return self.get_config(personnalite)["top_p"]
    
    def get_top_k(self, personnalite: str) -> int:
        """Récupère le top_k pour une personnalité"""
        return self.get_config(personnalite)["top_k"]
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Récupère toute la configuration"""
        return self.config.copy()
    
    def update_config(self, personnalite: str, **kwargs):
        """
        Met à jour la configuration d'une personnalité
        
        Args:
            personnalite: Nom de la personnalité
            **kwargs: Paramètres à mettre à jour
        """
        if personnalite in self.config:
            self.config[personnalite].update(kwargs)
    
    def validate_config(self) -> bool:
        """
        Valide la configuration actuelle
        
        Returns:
            True si la configuration est valide
        """
        for personnalite, config in self.config.items():
            # Vérifier la température
            if not (0.0 <= config["temperature"] <= 1.0):
                print(f"⚠️  Température invalide pour {personnalite}: {config['temperature']}")
                return False
            
            # Vérifier max_tokens
            if config["max_tokens"] <= 0:
                print(f"⚠️  Max tokens invalide pour {personnalite}: {config['max_tokens']}")
                return False
            
            # Vérifier top_p
            if not (0.0 <= config["top_p"] <= 1.0):
                print(f"⚠️  Top_p invalide pour {personnalite}: {config['top_p']}")
                return False
            
            # Vérifier top_k
            if config["top_k"] <= 0:
                print(f"⚠️  Top_k invalide pour {personnalite}: {config['top_k']}")
                return False
        
        return True

# Instance globale de configuration
personnalite_config = PersonnaliteConfig()

def get_personnalite_config(personnalite: str) -> Dict[str, Any]:
    """
    Fonction utilitaire pour récupérer la configuration d'une personnalité
    
    Args:
        personnalite: Nom de la personnalité
        
    Returns:
        Configuration de la personnalité
    """
    return personnalite_config.get_config(personnalite)

def get_personnalite_temperature(personnalite: str) -> float:
    """Fonction utilitaire pour récupérer la température d'une personnalité"""
    return personnalite_config.get_temperature(personnalite)

def get_personnalite_max_tokens(personnalite: str) -> int:
    """Fonction utilitaire pour récupérer le max_tokens d'une personnalité"""
    return personnalite_config.get_max_tokens(personnalite) 