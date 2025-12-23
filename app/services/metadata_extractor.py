# ==============================================================================
# FILE: app/services/metadata_extractor.py - Extraction de métadonnées fiscales
# ==============================================================================

import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FiscalMetadataExtractor:
    """
    Extrait les métadonnées fiscales des documents CGI
    (type d'impôt, régime fiscal, date de mise à jour)
    """
    
    def __init__(self):
        # Types d'impôts au Bénin
        self.impot_types = {
            "TVA": ["TVA", "taxe sur la valeur ajoutée", "taxe valeur ajoutée"],
            "IS": ["IS", "impôt sur les sociétés", "impôt sociétés"],
            "IRF": ["IRF", "impôt sur les revenus fonciers", "revenus fonciers"],
            "IRCM": ["IRCM", "impôt sur les revenus de capitaux mobiliers", "revenus capitaux mobiliers"],
            "IBA": ["IBA", "impôt sur les bénéfices agricoles", "bénéfices agricoles"],
            "ITS": ["ITS", "impôt sur les traitements et salaires", "traitements salaires"],
            "VPS": ["VPS", "versement de la patente simplifiée", "patente simplifiée"],
            "PATENTE": ["PATENTE", "patente", "versement patente"],
            "AIB": ["AIB", "avis d'imposition", "avis imposition"],
            "TPS": ["TPS", "taxe professionnelle simplifiée", "régime simplifié"]
        }
        
        # Régimes fiscaux
        self.regimes = {
            "REEL": ["régime réel", "régime réel normal", "régime réel simplifié", "réel"],
            "TPS": ["TPS", "taxe professionnelle simplifiée", "régime simplifié", "régime TPS"],
            "MICRO": ["micro", "micro-entreprise", "microentreprise"]
        }
        
        # Patterns pour détecter les dates de mise à jour
        self.date_patterns = [
            re.compile(r'(?:mis à jour|mise à jour|actualisé|modifié).*?(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})', re.IGNORECASE),
            re.compile(r'(?:version|v\.?)\s*(\d{4})', re.IGNORECASE),
            re.compile(r'(\d{4})\s*(?:code|CGI)', re.IGNORECASE),
        ]
    
    def extract_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Extrait les métadonnées fiscales d'un document
        
        Args:
            content: Contenu du document
            file_path: Chemin du fichier
            
        Returns:
            Dictionnaire de métadonnées fiscales
        """
        metadata = {
            "impot_types": [],
            "regime": None,
            "update_date": None,
            "fiscal_category": None,
            "has_calculations": False,
            "has_rates": False,
            "has_thresholds": False
        }
        
        content_lower = content.lower()
        file_name_lower = Path(file_path).name.lower()
        
        # Extraire les types d'impôts
        for impot_type, keywords in self.impot_types.items():
            for keyword in keywords:
                if keyword.lower() in content_lower or keyword.lower() in file_name_lower:
                    if impot_type not in metadata["impot_types"]:
                        metadata["impot_types"].append(impot_type)
                    break
        
        # Extraire le régime fiscal
        for regime, keywords in self.regimes.items():
            for keyword in keywords:
                if keyword.lower() in content_lower or keyword.lower() in file_name_lower:
                    metadata["regime"] = regime
                    break
            if metadata["regime"]:
                break
        
        # Extraire la date de mise à jour
        for pattern in self.date_patterns:
            match = pattern.search(content)
            if match:
                metadata["update_date"] = match.group(1)
                break
        
        # Détecter depuis le nom du fichier ou du répertoire
        if not metadata["update_date"]:
            # Chercher dans le chemin
            path_parts = Path(file_path).parts
            for part in path_parts:
                year_match = re.search(r'(\d{4})', part)
                if year_match:
                    metadata["update_date"] = year_match.group(1)
                    break
        
        # Détecter la catégorie fiscale depuis le chemin
        if "REGIME_REEL" in file_path.upper():
            metadata["regime"] = "REEL"
        elif "REGIME_TPS" in file_path.upper() or "TPS" in file_path.upper():
            metadata["regime"] = "TPS"
        
        # Détecter des caractéristiques supplémentaires
        metadata["has_calculations"] = bool(re.search(r'(?:calcul|formule|déterminer|détermination)', content_lower))
        metadata["has_rates"] = bool(re.search(r'\d+(?:,\d+)?\s*%', content))
        metadata["has_thresholds"] = bool(re.search(r'(?:seuil|plafond|plancher|limite)', content_lower))
        
        # Catégorie fiscale principale
        if metadata["impot_types"]:
            metadata["fiscal_category"] = metadata["impot_types"][0]
        elif metadata["regime"]:
            metadata["fiscal_category"] = metadata["regime"]
        
        return metadata
    
    def matches_filter(
        self, 
        metadata: Dict[str, Any], 
        filter_criteria: Dict[str, Any]
    ) -> bool:
        """
        Vérifie si les métadonnées correspondent aux critères de filtrage
        
        Args:
            metadata: Métadonnées du document
            filter_criteria: Critères de filtrage
            
        Returns:
            True si le document correspond aux critères
        """
        # Filtrage par type d'impôt
        if "impot_type" in filter_criteria:
            required_type = filter_criteria["impot_type"].upper()
            if required_type not in metadata.get("impot_types", []):
                return False
        
        # Filtrage par régime
        if "regime" in filter_criteria:
            required_regime = filter_criteria["regime"].upper()
            if metadata.get("regime") != required_regime:
                return False
        
        # Filtrage par date de mise à jour (année)
        if "update_year" in filter_criteria:
            update_date = metadata.get("update_date", "")
            if not update_date or str(filter_criteria["update_year"]) not in update_date:
                return False
        
        # Filtrage par catégorie fiscale
        if "fiscal_category" in filter_criteria:
            required_category = filter_criteria["fiscal_category"].upper()
            if metadata.get("fiscal_category") != required_category:
                return False
        
        # Filtrage par caractéristiques
        if "has_calculations" in filter_criteria:
            if metadata.get("has_calculations") != filter_criteria["has_calculations"]:
                return False
        
        if "has_rates" in filter_criteria:
            if metadata.get("has_rates") != filter_criteria["has_rates"]:
                return False
        
        return True

