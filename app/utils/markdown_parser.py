# ==============================================================================
# FILE: app/utils/markdown_parser.py - Parser spécialisé pour documents CGI
# ==============================================================================

import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import markdown
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class MarkdownParser:
    """Parser spécialisé pour les documents Markdown du Code Général des Impôts"""
    
    def __init__(self):
        self.md_processor = markdown.Markdown(extensions=[
            'toc', 'tables', 'fenced_code', 'attr_list'
        ])
        
        # Patterns pour identifier les éléments juridiques
        self.patterns = {
            'article': re.compile(r'(?:article|art\.?)\s*(\d+(?:[a-z]|bis|ter|quater)?)', re.IGNORECASE),
            'section': re.compile(r'section\s*(\d+|[ivx]+)', re.IGNORECASE),
            'paragraph': re.compile(r'(?:paragraphe|§)\s*(\d+)', re.IGNORECASE),
            'alinea': re.compile(r'alinéa\s*(\d+)', re.IGNORECASE),
            'code_reference': re.compile(r'CGI\s*art\.?\s*(\d+)', re.IGNORECASE),
            'legal_amount': re.compile(r'(\d+(?:\s?\d{3})*(?:,\d+)?)\s*€', re.IGNORECASE),
            'percentage': re.compile(r'(\d+(?:,\d+)?)\s*%'),
            'date': re.compile(r'\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})\b')
        }
        
        # Mots-clés par catégorie fiscale
        self.fiscal_keywords = {
            'revenus': [
                'revenus fonciers', 'revenus salariaux', 'revenus mobiliers',
                'plus-values', 'dividendes', 'intérêts', 'loyers'
            ],
            'deductions': [
                'déduction', 'charge déductible', 'crédit d\'impôt',
                'réduction d\'impôt', 'abattement', 'exonération'
            ],
            'entreprise': [
                'bénéfices industriels et commerciaux', 'BIC', 'BNC',
                'TVA', 'impôt sur les sociétés', 'IS', 'amortissement'
            ],
            'patrimoine': [
                'immobilier', 'ISF', 'IFI', 'succession', 'donation',
                'patrimoine', 'bien immobilier'
            ]
        }
    
    async def parse_document(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Parse un document Markdown en extrayant la structure et les métadonnées
        
        Args:
            content: Contenu Markdown brut
            file_path: Chemin du fichier source
            
        Returns:
            Document parsé avec métadonnées
        """
        try:
            # Informations de base
            file_name = Path(file_path).name
            
            # Convertir en HTML pour l'analyse
            html_content = self.md_processor.convert(content)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraire la structure
            structure = await self._extract_structure(soup, content)
            
            # Identifier les éléments juridiques
            legal_elements = await self._extract_legal_elements(content)
            
            # Catégoriser le contenu
            categories = await self._categorize_content(content)
            
            # Extraire les métadonnées
            metadata = await self._extract_metadata(content, file_path)
            
            document = {
                'file_name': file_name,
                'file_path': file_path,
                'raw_content': content,
                'html_content': html_content,
                'structure': structure,
                'legal_elements': legal_elements,
                'categories': categories,
                'metadata': metadata,
                'word_count': len(content.split()),
                'char_count': len(content)
            }
            
            logger.info(f"📄 Document parsé: {file_name} ({document['word_count']} mots)")
            return document
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing document {file_path}: {e}")
            return self._create_fallback_document(content, file_path)
    
    async def _extract_structure(self, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Extrait la structure hiérarchique du document"""
        structure = {
            'title': '',
            'headings': [],
            'sections': [],
            'toc': []
        }
        
        try:
            # Titre principal (premier H1 ou titre déduit du nom)
            h1 = soup.find('h1')
            if h1:
                structure['title'] = h1.get_text().strip()
            else:
                # Essayer de déduire du contenu
                first_line = content.split('\n')[0].strip()
                if first_line.startswith('#'):
                    structure['title'] = first_line.lstrip('#').strip()
                else:
                    structure['title'] = first_line[:100] + '...' if len(first_line) > 100 else first_line
            
            # Extraire tous les titres
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                structure['headings'].append({
                    'level': int(heading.name[1]),
                    'text': heading.get_text().strip(),
                    'id': heading.get('id', ''),
                    'position': len(structure['headings'])
                })
            
            # Créer la table des matières
            current_section = None
            for heading in structure['headings']:
                if heading['level'] <= 2:  # Sections principales
                    current_section = {
                        'title': heading['text'],
                        'level': heading['level'],
                        'subsections': []
                    }
                    structure['sections'].append(current_section)
                    structure['toc'].append(current_section)
                elif current_section and heading['level'] <= 4:
                    current_section['subsections'].append({
                        'title': heading['text'],
                        'level': heading['level']
                    })
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction structure: {e}")
        
        return structure
    
    async def _extract_legal_elements(self, content: str) -> Dict[str, List]:
        """Extrait les éléments juridiques du contenu"""
        legal_elements = {
            'articles': [],
            'sections': [],
            'paragraphs': [],
            'alineas': [],
            'references': [],
            'amounts': [],
            'percentages': [],
            'dates': []
        }
        
        try:
            # Articles
            for match in self.patterns['article'].finditer(content):
                article_num = match.group(1)
                context = self._get_context_around_match(content, match, 100)
                legal_elements['articles'].append({
                    'number': article_num,
                    'position': match.start(),
                    'context': context
                })
            
            # Sections
            for match in self.patterns['section'].finditer(content):
                section_num = match.group(1)
                context = self._get_context_around_match(content, match, 100)
                legal_elements['sections'].append({
                    'number': section_num,
                    'position': match.start(),
                    'context': context
                })
            
            # Références au CGI
            for match in self.patterns['code_reference'].finditer(content):
                ref = match.group(1)
                context = self._get_context_around_match(content, match, 150)
                legal_elements['references'].append({
                    'reference': f"CGI art. {ref}",
                    'position': match.start(),
                    'context': context
                })
            
            # Montants
            for match in self.patterns['legal_amount'].finditer(content):
                amount = match.group(1)
                context = self._get_context_around_match(content, match, 80)
                legal_elements['amounts'].append({
                    'amount': amount,
                    'position': match.start(),
                    'context': context
                })
            
            # Pourcentages
            for match in self.patterns['percentage'].finditer(content):
                percentage = match.group(1)
                context = self._get_context_around_match(content, match, 80)
                legal_elements['percentages'].append({
                    'percentage': percentage,
                    'position': match.start(),
                    'context': context
                })
            
            # Dates
            for match in self.patterns['date'].finditer(content):
                date = match.group(1)
                context = self._get_context_around_match(content, match, 60)
                legal_elements['dates'].append({
                    'date': date,
                    'position': match.start(),
                    'context': context
                })
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction éléments juridiques: {e}")
        
        return legal_elements
    
    async def _categorize_content(self, content: str) -> Dict[str, Any]:
        """Catégorise le contenu selon les thèmes fiscaux"""
        categories = {
            'primary_category': None,
            'secondary_categories': [],
            'confidence_scores': {},
            'detected_keywords': {}
        }
        
        try:
            content_lower = content.lower()
            
            # Compter les occurrences par catégorie
            category_scores = {}
            for category, keywords in self.fiscal_keywords.items():
                score = 0
                found_keywords = []
                
                for keyword in keywords:
                    count = content_lower.count(keyword.lower())
                    score += count
                    if count > 0:
                        found_keywords.append(keyword)
                
                if score > 0:
                    category_scores[category] = score
                    categories['detected_keywords'][category] = found_keywords
            
            # Déterminer la catégorie principale
            if category_scores:
                primary = max(category_scores, key=category_scores.get)
                categories['primary_category'] = primary
                
                # Normaliser les scores
                total_score = sum(category_scores.values())
                for category, score in category_scores.items():
                    confidence = score / total_score if total_score > 0 else 0
                    categories['confidence_scores'][category] = round(confidence, 3)
                    
                    if category != primary and confidence > 0.2:
                        categories['secondary_categories'].append(category)
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur catégorisation contenu: {e}")
        
        return categories
    
    async def _extract_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extrait les métadonnées du document"""
        metadata = {
            'file_size': 0,
            'creation_date': None,
            'language': 'fr',
            'document_type': 'legal',
            'complexity_score': 0,
            'readability_score': 0
        }
        
        try:
            # Taille du fichier
            if Path(file_path).exists():
                metadata['file_size'] = Path(file_path).stat().st_size
                metadata['creation_date'] = Path(file_path).stat().st_mtime
            
            # Score de complexité basé sur la structure
            complexity_factors = [
                len(self.patterns['article'].findall(content)) * 0.2,  # Nombre d'articles
                len(self.patterns['legal_amount'].findall(content)) * 0.1,  # Montants
                len(self.patterns['percentage'].findall(content)) * 0.1,  # Pourcentages
                content.count('alinéa') * 0.1,  # Alinéas
                content.count('paragraphe') * 0.1  # Paragraphes
            ]
            
            metadata['complexity_score'] = min(sum(complexity_factors), 10.0)
            
            # Score de lisibilité simple (basé sur la longueur des phrases)
            sentences = content.split('.')
            if sentences:
                avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
                metadata['readability_score'] = max(0, 10 - (avg_sentence_length / 10))
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction métadonnées: {e}")
        
        return metadata
    
    def _get_context_around_match(self, text: str, match: re.Match, context_length: int = 100) -> str:
        """Extrait le contexte autour d'un match regex"""
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        context = text[start:end]
        
        # Nettoyer les retours à la ligne multiples
        context = re.sub(r'\n+', ' ', context)
        context = re.sub(r'\s+', ' ', context)
        
        return context.strip()
    
    def _create_fallback_document(self, content: str, file_path: str) -> Dict[str, Any]:
        """Crée un document de base en cas d'erreur de parsing"""
        file_name = Path(file_path).name
        
        return {
            'file_name': file_name,
            'file_path': file_path,
            'raw_content': content,
            'html_content': content,
            'structure': {
                'title': file_name,
                'headings': [],
                'sections': [],
                'toc': []
            },
            'legal_elements': {
                'articles': [],
                'sections': [],
                'paragraphs': [],
                'alineas': [],
                'references': [],
                'amounts': [],
                'percentages': [],
                'dates': []
            },
            'categories': {
                'primary_category': None,
                'secondary_categories': [],
                'confidence_scores': {},
                'detected_keywords': {}
            },
            'metadata': {
                'file_size': len(content),
                'creation_date': None,
                'language': 'fr',
                'document_type': 'legal',
                'complexity_score': 1.0,
                'readability_score': 5.0
            },
            'word_count': len(content.split()),
            'char_count': len(content)
        }
    
    def extract_article_references(self, text: str) -> List[Dict[str, Any]]:
        """Extrait toutes les références d'articles d'un texte"""
        references = []
        
        for match in self.patterns['article'].finditer(text):
            article_num = match.group(1)
            context = self._get_context_around_match(text, match, 200)
            
            references.append({
                'article_number': article_num,
                'full_reference': match.group(0),
                'position': match.start(),
                'context': context,
                'confidence': 1.0 if 'article' in match.group(0).lower() else 0.8
            })
        
        return references
    
    def extract_legal_amounts_with_context(self, text: str) -> List[Dict[str, Any]]:
        """Extrait les montants légaux avec leur contexte détaillé"""
        amounts = []
        
        for match in self.patterns['legal_amount'].finditer(text):
            amount_str = match.group(1)
            context = self._get_context_around_match(text, match, 300)
            
            # Essayer de déterminer le type de montant
            amount_type = self._classify_amount_type(context)
            
            amounts.append({
                'amount': amount_str,
                'amount_numeric': self._parse_amount_to_number(amount_str),
                'type': amount_type,
                'context': context,
                'position': match.start(),
                'currency': 'EUR'
            })
        
        return amounts
    
    def _classify_amount_type(self, context: str) -> str:
        """Classifie le type de montant basé sur le contexte"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['seuil', 'plafond', 'limite']):
            return 'threshold'
        elif any(word in context_lower for word in ['amende', 'pénalité', 'sanction']):
            return 'penalty'
        elif any(word in context_lower for word in ['déduction', 'abattement', 'réduction']):
            return 'deduction'
        elif any(word in context_lower for word in ['minimum', 'plancher']):
            return 'minimum'
        elif any(word in context_lower for word in ['maximum', 'plafond']):
            return 'maximum'
        else:
            return 'amount'
    
    def _parse_amount_to_number(self, amount_str: str) -> float:
        """Convertit une chaîne de montant en nombre"""
        try:
            # Supprimer les espaces et remplacer la virgule par un point
            clean_amount = amount_str.replace(' ', '').replace(',', '.')
            return float(clean_amount)
        except ValueError:
            return 0.0
    
    def validate_legal_structure(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et enrichit la structure juridique du document"""
        validation = {
            'is_valid_legal_document': False,
            'confidence_score': 0.0,
            'issues': [],
            'suggestions': []
        }
        
        try:
            # Vérifications de base
            has_articles = len(document['legal_elements']['articles']) > 0
            has_legal_content = any(keyword in document['raw_content'].lower() 
                                  for keywords in self.fiscal_keywords.values() 
                                  for keyword in keywords)
            has_structure = len(document['structure']['headings']) > 0
            
            # Calcul du score de confiance
            confidence_factors = []
            
            if has_articles:
                confidence_factors.append(0.4)
            else:
                validation['issues'].append("Aucun article détecté")
                validation['suggestions'].append("Vérifier la numérotation des articles")
            
            if has_legal_content:
                confidence_factors.append(0.3)
            else:
                validation['issues'].append("Peu de contenu juridique fiscal détecté")
                validation['suggestions'].append("Enrichir avec plus de terminologie fiscale")
            
            if has_structure:
                confidence_factors.append(0.2)
            else:
                validation['issues'].append("Structure de document faible")
                validation['suggestions'].append("Améliorer la hiérarchisation avec des titres")
            
            # Vérifier la cohérence des références
            references = document['legal_elements']['references']
            if references:
                confidence_factors.append(0.1)
            else:
                validation['suggestions'].append("Ajouter des références croisées vers d'autres articles")
            
            validation['confidence_score'] = sum(confidence_factors)
            validation['is_valid_legal_document'] = validation['confidence_score'] > 0.5
            
        except Exception as e:
            logger.error(f"❌ Erreur validation structure légale: {e}")
            validation['issues'].append(f"Erreur de validation: {str(e)}")
        
        return validation