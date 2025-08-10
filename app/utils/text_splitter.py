# ==============================================================================
# FILE: app/utils/text_splitter.py - Découpage intelligent pour documents CGI
# ==============================================================================

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import tiktoken

logger = logging.getLogger(__name__)

class TextSplitter:
    """Découpage intelligent de texte pour documents juridiques du CGI"""
    
    def __init__(self, 
                 max_chunk_size: int = 1000,
                 min_chunk_size: int = 100,
                 overlap_size: int = 50,
                 preserve_structure: bool = True):
        """
        Initialize le splitter
        
        Args:
            max_chunk_size: Taille maximale d'un chunk en caractères
            min_chunk_size: Taille minimale d'un chunk
            overlap_size: Taille de chevauchement entre chunks
            preserve_structure: Préserver la structure juridique
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_size = overlap_size
        self.preserve_structure = preserve_structure
        
        # Encodeur pour compter les tokens (approximation GPT)
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Patterns pour identifier les séparateurs naturels
        self.separators = {
            # Ordre de priorité décroissant
            'article_start': re.compile(r'^(#{1,2}\s*)?(?:article|art\.?)\s*\d+', re.MULTILINE | re.IGNORECASE),
            'section_start': re.compile(r'^(#{1,3}\s*)?section\s*\d+', re.MULTILINE | re.IGNORECASE),
            'paragraph_numbered': re.compile(r'^\d+°?\s*[-\.\)]\s*', re.MULTILINE),
            'paragraph_lettered': re.compile(r'^[a-z]\)\s*', re.MULTILINE | re.IGNORECASE),
            'alinea': re.compile(r'^\s*[A-Z]', re.MULTILINE),  # Alinéa commençant par majuscule
            'double_newline': re.compile(r'\n\s*\n'),
            'sentence_end': re.compile(r'[.!?]\s+'),
            'comma_space': re.compile(r',\s+')
        }
        
        # Patterns pour détecter les éléments à ne pas couper
        self.preserve_patterns = {
            'article_reference': re.compile(r'(?:article|art\.?)\s*\d+(?:[a-z]|bis|ter|quater)?', re.IGNORECASE),
            'legal_amount': re.compile(r'\d+(?:\s?\d{3})*(?:,\d+)?\s*€'),
            'percentage': re.compile(r'\d+(?:,\d+)?\s*%'),
            'date': re.compile(r'\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b'),
            'enumeration': re.compile(r'^\s*(?:\d+°?|[a-z]\))', re.MULTILINE)
        }
    
    async def split_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Découpe un document parsé en chunks intelligents
        
        Args:
            document: Document parsé par MarkdownParser
            
        Returns:
            Liste de chunks avec métadonnées
        """
        try:
            content = document['raw_content']
            structure = document.get('structure', {})
            legal_elements = document.get('legal_elements', {})
            
            if self.preserve_structure and structure.get('sections'):
                # Découpage basé sur la structure
                chunks = await self._split_by_structure(document)
            else:
                # Découpage basé sur le contenu
                chunks = await self._split_by_content(content)
            
            # Enrichir chaque chunk avec des métadonnées
            enriched_chunks = []
            for i, chunk in enumerate(chunks):
                enriched_chunk = await self._enrich_chunk(
                    chunk, i, document, legal_elements
                )
                enriched_chunks.append(enriched_chunk)
            
            # Post-traitement : fusionner les chunks trop petits
            final_chunks = await self._post_process_chunks(enriched_chunks)
            
            logger.info(f"📄 Document découpé en {len(final_chunks)} chunks")
            return final_chunks
            
        except Exception as e:
            logger.error(f"❌ Erreur découpage document: {e}")
            # Fallback : découpage simple par taille
            return await self._fallback_split(document['raw_content'])
    
    async def _split_by_structure(self, document: Dict[str, Any]) -> List[Dict[str, str]]:
        """Découpage basé sur la structure hiérarchique du document"""
        chunks = []
        content = document['raw_content']
        sections = document['structure']['sections']
        
        if not sections:
            return await self._split_by_content(content)
        
        # Diviser le contenu par sections principales
        section_contents = await self._extract_section_contents(content, sections)
        
        for section_info in section_contents:
            section_text = section_info['content']
            section_title = section_info['title']
            
            # Si la section est trop grande, la subdiviser
            if len(section_text) > self.max_chunk_size:
                sub_chunks = await self._split_large_section(section_text, section_title)
                chunks.extend(sub_chunks)
            else:
                chunks.append({
                    'text': section_text,
                    'title': section_title,
                    'type': 'section',
                    'section': section_title
                })
        
        return chunks
    
    async def _extract_section_contents(self, content: str, sections: List[Dict]) -> List[Dict]:
        """Extrait le contenu de chaque section"""
        section_contents = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Vérifier si c'est un nouveau titre de section
            is_section_header = False
            for section in sections:
                if section['title'].lower() in line.lower() and (
                    line.startswith('#') or 
                    line.strip().isupper() or
                    len(line.strip()) < 100
                ):
                    is_section_header = True
                    new_section_title = section['title']
                    break
            
            if is_section_header:
                # Sauvegarder la section précédente
                if current_section and current_content:
                    section_contents.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip()
                    })
                
                # Commencer une nouvelle section
                current_section = new_section_title
                current_content = [line]
            else:
                current_content.append(line)
        
        # Sauvegarder la dernière section
        if current_section and current_content:
            section_contents.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip()
            })
        
        # Si aucune section trouvée, traiter tout comme une section
        if not section_contents:
            section_contents.append({
                'title': "Document complet",
                'content': content
            })
        
        return section_contents
    
    async def _split_large_section(self, text: str, section_title: str) -> List[Dict[str, str]]:
        """Découpe une section trop grande en respectant la structure"""
        chunks = []
        
        # Essayer de découper par articles d'abord
        article_splits = list(self.separators['article_start'].finditer(text))
        
        if len(article_splits) > 1:
            # Découper par articles
            for i, match in enumerate(article_splits):
                start_pos = match.start()
                end_pos = article_splits[i + 1].start() if i + 1 < len(article_splits) else len(text)
                
                article_text = text[start_pos:end_pos].strip()
                article_title = match.group(0)
                
                if len(article_text) > self.max_chunk_size:
                    # Article encore trop grand, découper davantage
                    sub_chunks = await self._split_by_content(article_text)
                    for j, sub_chunk in enumerate(sub_chunks):
                        sub_chunk['title'] = f"{article_title} (partie {j+1})"
                        sub_chunk['section'] = section_title
                        sub_chunk['article'] = article_title
                        chunks.append(sub_chunk)
                else:
                    chunks.append({
                        'text': article_text,
                        'title': article_title,
                        'section': section_title,
                        'article': article_title,
                        'type': 'article'
                    })
        else:
            # Pas d'articles, découpage par contenu
            content_chunks = await self._split_by_content(text)
            for i, chunk in enumerate(content_chunks):
                chunk['title'] = f"{section_title} (partie {i+1})"
                chunk['section'] = section_title
                chunks.append(chunk)
        
        return chunks
    
    async def _split_by_content(self, text: str) -> List[Dict[str, str]]:
        """Découpage intelligent basé sur le contenu et les séparateurs naturels"""
        chunks = []
        
        # Nettoyer le texte
        text = self._clean_text(text)
        
        if len(text) <= self.max_chunk_size:
            return [{'text': text, 'type': 'content'}]
        
        # Essayer les différents séparateurs par ordre de priorité
        for separator_name, pattern in self.separators.items():
            if separator_name in ['article_start', 'section_start']:
                continue  # Déjà traité dans split_by_structure
            
            splits = await self._try_split_with_separator(text, pattern, separator_name)
            if splits:
                return splits
        
        # Fallback : découpage par taille fixe avec chevauchement
        return await self._split_by_size(text)
    
    async def _try_split_with_separator(self, text: str, pattern: re.Pattern, 
                                      separator_name: str) -> Optional[List[Dict[str, str]]]:
        """Essaie de découper avec un séparateur spécifique"""
        splits = list(pattern.finditer(text))
        
        if len(splits) < 2:
            return None
        
        chunks = []
        last_end = 0
        
        for i, match in enumerate(splits[1:], 1):  # Commencer au 2ème match
            start_pos = last_end
            end_pos = match.start()
            
            chunk_text = text[start_pos:end_pos].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                # Ajouter un chevauchement avec le chunk précédent
                if chunks and self.overlap_size > 0:
                    overlap_start = max(0, len(chunk_text) - self.overlap_size)
                    overlap = chunk_text[overlap_start:]
                    chunk_text = chunks[-1]['text'][-self.overlap_size:] + " " + chunk_text
                
                chunks.append({
                    'text': chunk_text,
                    'type': separator_name,
                    'separator_used': separator_name
                })
                
                last_end = match.start()
        
        # Ajouter le dernier chunk
        if last_end < len(text):
            final_chunk = text[last_end:].strip()
            if len(final_chunk) >= self.min_chunk_size:
                if chunks and self.overlap_size > 0:
                    final_chunk = chunks[-1]['text'][-self.overlap_size:] + " " + final_chunk
                
                chunks.append({
                    'text': final_chunk,
                    'type': separator_name,
                    'separator_used': separator_name
                })
        
        # Vérifier que les chunks ne sont pas trop grands
        valid_chunks = []
        for chunk in chunks:
            if len(chunk['text']) > self.max_chunk_size:
                # Subdiviser davantage
                sub_chunks = await self._split_by_size(chunk['text'])
                for sub_chunk in sub_chunks:
                    sub_chunk['parent_type'] = separator_name
                    valid_chunks.append(sub_chunk)
            else:
                valid_chunks.append(chunk)
        
        return valid_chunks if valid_chunks else None
    
    async def _split_by_size(self, text: str) -> List[Dict[str, str]]:
        """Découpage par taille fixe avec préservation des mots"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 pour l'espace
            
            if current_length + word_length > self.max_chunk_size and current_chunk:
                # Finaliser le chunk actuel
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'type': 'size_split',
                    'word_count': len(current_chunk)
                })
                
                # Commencer le nouveau chunk avec chevauchement
                if self.overlap_size > 0:
                    overlap_words = current_chunk[-self.overlap_size:]
                    current_chunk = overlap_words + [word]
                    current_length = sum(len(w) + 1 for w in current_chunk)
                else:
                    current_chunk = [word]
                    current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Ajouter le dernier chunk
        if current_chunk:
            chunks.append({
                'text': ' '.join(current_chunk),
                'type': 'size_split',
                'word_count': len(current_chunk)
            })
        
        return chunks
    
    async def _enrich_chunk(self, chunk: Dict[str, str], index: int, 
                          document: Dict[str, Any], legal_elements: Dict) -> Dict[str, Any]:
        """Enrichit un chunk avec des métadonnées"""
        text = chunk['text']
        
        enriched = {
            'text': text,
            'chunk_index': index,
            'title': chunk.get('title', f"Chunk {index + 1}"),
            'section': chunk.get('section', ''),
            'article': chunk.get('article', ''),
            'type': chunk.get('type', 'content'),
            'word_count': len(text.split()),
            'char_count': len(text),
            'token_count': await self._count_tokens(text),
            'keywords': await self._extract_keywords(text),
            'legal_references': await self._find_legal_references_in_chunk(text, legal_elements),
            'metadata': {
                'separator_used': chunk.get('separator_used', 'none'),
                'parent_type': chunk.get('parent_type', ''),
                'has_amounts': bool(re.search(r'\d+(?:\s?\d{3})*(?:,\d+)?\s*€', text)),
                'has_percentages': bool(re.search(r'\d+(?:,\d+)?\s*%', text)),
                'has_dates': bool(re.search(r'\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b', text)),
                'complexity_score': await self._calculate_chunk_complexity(text)
            }
        }
        
        return enriched
    
    async def _count_tokens(self, text: str) -> int:
        """Compte approximativement les tokens dans un texte"""
        try:
            return len(self.tokenizer.encode(text))
        except:
            # Approximation grossière : 1 token ≈ 4 caractères en français
            return len(text) // 4
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés importants d'un chunk"""
        # Mots-clés juridiques courants
        legal_keywords = [
            'article', 'alinéa', 'paragraphe', 'section', 'chapitre',
            'impôt', 'taxe', 'déduction', 'crédit', 'abattement',
            'revenus', 'bénéfices', 'plus-values', 'patrimoine',
            'déclaration', 'assiette', 'barème', 'taux'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in legal_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # Limiter à 10 mots-clés
    
    async def _find_legal_references_in_chunk(self, text: str, legal_elements: Dict) -> List[str]:
        """Trouve les références légales dans un chunk"""
        references = []
        
        # Articles mentionnés
        for article in legal_elements.get('articles', []):
            if article['number'] in text or f"article {article['number']}" in text.lower():
                references.append(f"Art. {article['number']}")
        
        # Références CGI
        for ref in legal_elements.get('references', []):
            if ref['reference'].lower() in text.lower():
                references.append(ref['reference'])
        
        return references
    
    async def _calculate_chunk_complexity(self, text: str) -> float:
        """Calcule un score de complexité pour un chunk"""
        factors = []
        
        # Longueur des phrases
        sentences = text.split('.')
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            factors.append(min(avg_sentence_length / 20, 1.0))
        
        # Density de références juridiques
        legal_pattern_count = sum(1 for pattern in self.preserve_patterns.values() 
                                if pattern.search(text))
        factors.append(min(legal_pattern_count / 5, 1.0))
        
        # Présence de montants et pourcentages
        has_numbers = bool(re.search(r'\d+', text))
        factors.append(0.5 if has_numbers else 0.0)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    async def _post_process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-traitement des chunks : fusion des petits chunks"""
        if not chunks:
            return chunks
        
        processed_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
                continue
            
            # Si le chunk actuel est trop petit et peut être fusionné
            current_size = len(current_chunk['text'])
            chunk_size = len(chunk['text'])
            
            if (current_size < self.min_chunk_size and 
                current_size + chunk_size <= self.max_chunk_size and
                current_chunk.get('section') == chunk.get('section')):
                
                # Fusionner les chunks
                current_chunk['text'] += '\n\n' + chunk['text']
                current_chunk['word_count'] += chunk['word_count']
                current_chunk['char_count'] += chunk['char_count']
                current_chunk['token_count'] += chunk['token_count']
                current_chunk['keywords'] = list(set(
                    current_chunk['keywords'] + chunk['keywords']
                ))[:10]
                current_chunk['type'] = 'merged'
            else:
                # Finaliser le chunk actuel
                processed_chunks.append(current_chunk)
                current_chunk = chunk
        
        # Ajouter le dernier chunk
        if current_chunk:
            processed_chunks.append(current_chunk)
        
        return processed_chunks
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte avant découpage"""
        # Supprimer les retours à la ligne multiples
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Normaliser les espaces
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Supprimer les espaces en début/fin de lignes
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        return text.strip()
    
    async def _fallback_split(self, content: str) -> List[Dict[str, Any]]:
        """Découpage de secours en cas d'erreur"""
        chunks = await self._split_by_size(content)
        
        return [{
            'text': chunk['text'],
            'chunk_index': i,
            'title': f"Chunk {i + 1}",
            'section': '',
            'article': '',
            'type': 'fallback',
            'word_count': chunk['word_count'],
            'char_count': len(chunk['text']),
            'token_count': len(chunk['text']) // 4,  # Approximation
            'keywords': [],
            'legal_references': [],
            'metadata': {
                'separator_used': 'fallback',
                'parent_type': 'error',
                'has_amounts': False,
                'has_percentages': False,
                'has_dates': False,
                'complexity_score': 0.5
            }
        } for i, chunk in enumerate(chunks)]