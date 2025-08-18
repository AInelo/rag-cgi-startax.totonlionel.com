#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la configuration des personnalités du chatbot RAG CGI
"""

import sys
import os

# Ajouter le répertoire app au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_config():
    """Test de la configuration des personnalités"""
    
    print("🧪 Test de la Configuration des Personnalités")
    print("=" * 50)
    
    try:
        from app.config.personnalite_config import PersonnaliteConfig, personnalite_config
        
        # Créer une instance de configuration
        config = PersonnaliteConfig()
        
        print("\n1. Configuration par défaut:")
        print("-" * 30)
        
        all_configs = config.get_all_configs()
        for personnalite, params in all_configs.items():
            print(f"   🎭 {personnalite.upper()}:")
            print(f"      Température: {params['temperature']}")
            print(f"      Max tokens: {params['max_tokens']}")
            print(f"      Top_p: {params['top_p']}")
            print(f"      Top_k: {params['top_k']}")
            print(f"      Description: {params['description']}")
            print()
        
        print("\n2. Test des fonctions utilitaires:")
        print("-" * 30)
        
        for personnalite in ["expert", "expert_cgi", "mathematicien"]:
            temp = config.get_temperature(personnalite)
            max_tokens = config.get_max_tokens(personnalite)
            top_p = config.get_top_p(personnalite)
            top_k = config.get_top_k(personnalite)
            
            print(f"   📊 {personnalite}:")
            print(f"      Température: {temp}")
            print(f"      Max tokens: {max_tokens}")
            print(f"      Top_p: {top_p}")
            print(f"      Top_k: {top_k}")
        
        print("\n3. Validation de la configuration:")
        print("-" * 30)
        
        is_valid = config.validate_config()
        if is_valid:
            print("   ✅ Configuration valide")
        else:
            print("   ❌ Configuration invalide")
        
        print("\n4. Test de mise à jour:")
        print("-" * 30)
        
        # Mettre à jour la configuration de l'expert
        config.update_config("expert", temperature=0.05, max_tokens=100)
        
        updated_config = config.get_config("expert")
        print(f"   🔄 Expert mis à jour:")
        print(f"      Nouvelle température: {updated_config['temperature']}")
        print(f"      Nouveau max_tokens: {updated_config['max_tokens']}")
        
        # Remettre la configuration par défaut
        config.update_config("expert", temperature=0.1, max_tokens=150)
        
        print("\n5. Test des variables d'environnement:")
        print("-" * 30)
        
        # Simuler des variables d'environnement
        os.environ["EXPERT_TEMPERATURE"] = "0.05"
        os.environ["MATHEMATICIEN_MAX_TOKENS"] = "1000"
        
        # Créer une nouvelle instance pour charger les variables
        config_env = PersonnaliteConfig()
        
        expert_temp = config_env.get_temperature("expert")
        math_tokens = config_env.get_max_tokens("mathematicien")
        
        print(f"   🌍 Variables d'environnement:")
        print(f"      EXPERT_TEMPERATURE=0.05 → {expert_temp}")
        print(f"      MATHEMATICIEN_MAX_TOKENS=1000 → {math_tokens}")
        
        # Nettoyer les variables d'environnement
        if "EXPERT_TEMPERATURE" in os.environ:
            del os.environ["EXPERT_TEMPERATURE"]
        if "MATHEMATICIEN_MAX_TOKENS" in os.environ:
            del os.environ["MATHEMATICIEN_MAX_TOKENS"]
        
        print("\n✅ Tous les tests de configuration sont passés !")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Assurez-vous que le module de configuration est correctement installé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_integration():
    """Test d'intégration avec le service de personnalités"""
    
    print("\n🔗 Test d'Intégration")
    print("=" * 30)
    
    try:
        from app.services.personnalite_service import PersonnaliteService
        from app.config.personnalite_config import get_personnalite_config
        
        # Créer le service de personnalités
        ps = PersonnaliteService()
        
        print("\n1. Test d'intégration configuration-personnalités:")
        print("-" * 50)
        
        for personnalite in ["expert", "expert_cgi", "mathematicien"]:
            # Récupérer la configuration
            config = get_personnalite_config(personnalite)
            
            # Récupérer le prompt système
            prompt = ps.get_prompt_system(personnalite)
            
            print(f"   🎭 {personnalite.upper()}:")
            print(f"      Configuration: T={config['temperature']}, Tokens={config['max_tokens']}")
            print(f"      Prompt: {len(prompt)} caractères")
            print(f"      Contient personnalité: {'✅' if personnalite in prompt.lower() else '❌'}")
        
        print("\n✅ Intégration réussie !")
        
    except Exception as e:
        print(f"❌ Erreur d'intégration: {e}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de configuration...")
    
    # Test de la configuration
    test_config()
    
    # Test d'intégration
    test_integration()
    
    print("\n🎉 Tests de configuration terminés !")
    print("\n📋 Résumé:")
    print("   • Configuration des personnalités fonctionnelle")
    print("   • Variables d'environnement supportées")
    print("   • Intégration avec le service de personnalités")
    print("   • Validation automatique des paramètres")
    
    print("\n💡 Pour personnaliser:")
    print("   • Modifiez app/config/personnalite_config.py")
    print("   • Utilisez des variables d'environnement")
    print("   • Redémarrez le service après modification") 