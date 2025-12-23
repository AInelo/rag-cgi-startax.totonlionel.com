# ==============================================================================
# FILE: app/services/rag_service.py - Service RAG Principal
# ==============================================================================

import asyncio
import logging
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
import uuid

from app.services.llm_service_gemini import GeminiLLMService, create_gemini_service
from app.services.embedding_service import EmbeddingService
from app.services.reranker_service import RerankerService
from app.services.metadata_extractor import FiscalMetadataExtractor
from app.database.vector_store import VectorStore
from app.utils.markdown_parser import MarkdownParser
from app.utils.text_splitter import TextSplitter

logger = logging.getLogger(__name__)

class DocumentSource:
    def __init__(self, title: str, section: str, article: str, content: str, 
                 source_file: str, relevance_score: float = 0.0):
        self.title = title
        self.section = section
        self.article = article
        self.content = content
        self.source_file = source_file
        self.relevance_score = relevance_score
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "section": self.section,
            "article": self.article,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "source_file": self.source_file,
            "relevance_score": round(self.relevance_score, 3),
            "metadata": self.metadata
        }

class RAGService:
    def __init__(self, api_key: str = None):
        """
        Service RAG pour le Code Général des Impôts
        
        Args:
            api_key: Clé API Google AI Studio (GOOGLE_API_KEY)
        """
        # Utiliser la clé Google AI Studio pour Gemini
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        if not self.api_key:
            logger.warning("⚠️ Aucune clé API Google AI Studio trouvée. Le service LLM ne fonctionnera pas.")
        
        # Configuration du service LLM Gemini
        llm_config = {
            'api_key': self.api_key,
            'model_name': 'gemini-2.0-flash',  # Modèle gratuit par défaut
            'temperature': 0.3,  # Température basse pour des réponses fiscales précises
            'max_output_tokens': 2048
        }
        
        # Initialiser directement le service Gemini
        try:
            self.llm_service = create_gemini_service(llm_config)
            logger.info(f"✅ Service LLM Gemini initialisé: {llm_config['model_name']}")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Gemini: {e}")
            self.llm_service = None
        
        self.embedding_service = EmbeddingService(self.api_key)
        self.vector_store = VectorStore()
        self.markdown_parser = MarkdownParser()
        self.text_splitter = TextSplitter()
        
        # Nouveaux services
        self.reranker_service = RerankerService()
        self.metadata_extractor = FiscalMetadataExtractor()
        
        self.is_initialized = False
        self.query_cache = {}  # Cache des requêtes récentes
        self.query_logs = []   # Logs pour analytics
        
    async def initialize(self):
        """Initialise tous les composants du service RAG"""
        if self.is_initialized:
            return
            
        logger.info("🚀 Initialisation du service RAG...")
        
        try:
            # Initialiser les composants
            # Le service d'embeddings est maintenant initialisé automatiquement
            await self.vector_store.initialize()
            
            # Initialiser le re-ranker
            await self.reranker_service.initialize()
            
            # Vérifier que le service LLM est fonctionnel
            if self.llm_service:
                try:
                    health_check = self.llm_service.health_check()
                    if health_check.get("status") == "healthy":
                        logger.info(f"✅ Service LLM Gemini opérationnel: {health_check.get('model')}")
                    else:
                        logger.warning(f"⚠️ Service LLM en état dégradé: {health_check}")
                except Exception as e:
                    logger.error(f"❌ Erreur vérification service LLM: {e}")
            else:
                logger.error("❌ Service LLM Gemini non initialisé")
            
            self.is_initialized = True
            logger.info("✅ Service RAG initialisé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation RAG: {e}")
            raise
    
    async def index_documents(self, documents_path: str):
        """
        Indexe tous les documents Markdown du répertoire spécifié
        
        Args:
            documents_path: Chemin vers les documents CGI
        """
        if not self.is_initialized:
            await self.initialize()
            
        logger.info(f"📚 Début d'indexation: {documents_path}")
        start_time = time.time()
        
        try:
            # Vérifier que le répertoire existe
            if not os.path.exists(documents_path):
                raise FileNotFoundError(f"Répertoire non trouvé: {documents_path}")
            
            # Parcourir tous les fichiers .md
            markdown_files = []
            for root, dirs, files in os.walk(documents_path):
                for file in files:
                    if file.endswith('.md'):
                        markdown_files.append(os.path.join(root, file))
            
            if not markdown_files:
                raise ValueError(f"Aucun fichier .md trouvé dans {documents_path}")
            
            logger.info(f"📄 {len(markdown_files)} fichiers Markdown trouvés")
            
            # Traiter chaque fichier
            all_chunks = []
            for file_path in markdown_files:
                try:
                    chunks = await self._process_markdown_file(file_path)
                    all_chunks.extend(chunks)
                    logger.info(f"✅ {file_path}: {len(chunks)} chunks créés")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur traitement {file_path}: {e}")
                    continue
            
            if not all_chunks:
                raise ValueError("Aucun chunk créé à partir des documents")
            
            logger.info(f"🔢 Total: {len(all_chunks)} chunks à indexer")
            
            # Créer les embeddings en batch
            texts = [chunk['content'] for chunk in all_chunks]
            logger.info("🧠 Génération des embeddings...")
            embeddings = await self.embedding_service.get_embeddings(texts)
            
            # Sauvegarder dans la base vectorielle
            logger.info("💾 Sauvegarde dans la base vectorielle...")
            await self.vector_store.add_documents(all_chunks, embeddings)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Indexation terminée en {processing_time:.2f}s")
            
            # Statistiques
            stats = {
                "files_processed": len(markdown_files),
                "chunks_created": len(all_chunks),
                "processing_time": processing_time,
                "average_chunk_size": sum(len(chunk['content']) for chunk in all_chunks) / len(all_chunks),
                "indexed_at": datetime.now().isoformat()
            }
            
            await self.vector_store.save_indexing_stats(stats)
            
        except Exception as e:
            logger.error(f"❌ Erreur durant l'indexation: {e}")
            raise
    
    async def _process_markdown_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Traite un fichier Markdown et le découpe en chunks
        
        Args:
            file_path: Chemin vers le fichier Markdown
            
        Returns:
            Liste des chunks avec métadonnées
        """
        try:
            # Lire le fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parser le Markdown
            parsed_doc = await self.markdown_parser.parse_document(content, file_path)
            
            # Extraire les métadonnées fiscales
            fiscal_metadata = self.metadata_extractor.extract_metadata(content, file_path)
            
            # Découper en chunks intelligents
            chunks = await self.text_splitter.split_document(parsed_doc)
            
            # Enrichir avec des métadonnées
            enriched_chunks = []
            for i, chunk in enumerate(chunks):
                enriched_chunk = {
                    "id": f"{os.path.basename(file_path)}_{i}",
                    "content": chunk["text"],
                    "title": chunk.get("title", os.path.basename(file_path)),
                    "section": chunk.get("section", ""),
                    "article": chunk.get("article", ""),
                    "source_file": file_path,
                    "chunk_index": i,
                    "metadata": {
                        "file_size": os.path.getsize(file_path),
                        "created_at": datetime.now().isoformat(),
                        "chunk_type": chunk.get("type", "text"),
                        "legal_references": chunk.get("legal_references", []),
                        "keywords": chunk.get("keywords", []),
                        # Nouvelles métadonnées fiscales
                        "impot_types": fiscal_metadata.get("impot_types", []),
                        "regime": fiscal_metadata.get("regime"),
                        "update_date": fiscal_metadata.get("update_date"),
                        "fiscal_category": fiscal_metadata.get("fiscal_category"),
                        "has_calculations": fiscal_metadata.get("has_calculations", False),
                        "has_rates": fiscal_metadata.get("has_rates", False),
                        "has_thresholds": fiscal_metadata.get("has_thresholds", False)
                    }
                }
                enriched_chunks.append(enriched_chunk)
            
            return enriched_chunks
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement fichier {file_path}: {e}")
            return []
    
    async def search_relevant_sources(
        self, 
        question: str, 
        max_sources: int = 3, 
        context_type: str = "general",
        filter_criteria: Optional[Dict[str, Any]] = None,
        use_reranking: bool = True
    ) -> List[DocumentSource]:
        """
        Recherche les sources les plus pertinentes pour une question
        
        Args:
            question: Question de l'utilisateur
            max_sources: Nombre maximum de sources à retourner
            context_type: Type de contexte (general, particulier, entreprise, fiscal)
            filter_criteria: Critères de filtrage avancé (impot_type, regime, update_year, etc.)
            use_reranking: Utiliser le re-ranking avec cross-encoder
            
        Returns:
            Liste des sources pertinentes triées par score
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Créer l'embedding de la question
            question_embedding = await self.embedding_service.get_embedding(question)
            
            # Rechercher dans la base vectorielle avec filtrage
            # Récupérer plus de résultats pour le re-ranking
            initial_top_k = max_sources * 3 if use_reranking else max_sources * 2
            
            results = await self.vector_store.similarity_search(
                question_embedding, 
                top_k=initial_top_k,
                filter_criteria=filter_criteria
            )
            
            # Re-ranking avec cross-encoder si disponible
            if use_reranking and self.reranker_service.is_available():
                logger.info("🔄 Re-ranking des résultats avec cross-encoder...")
                results = await self.reranker_service.rerank(
                    query=question,
                    documents=results,
                    top_k=max_sources * 2  # Garder plus de résultats pour le filtrage contextuel
                )
            
            # Convertir en objets DocumentSource
            sources = []
            for result in results:
                source = DocumentSource(
                    title=result.get("title", ""),
                    section=result.get("section", ""),
                    article=result.get("article", ""),
                    content=result.get("content", ""),
                    source_file=result.get("source_file", ""),
                    relevance_score=result.get("similarity_score", 0.0)
                )
                source.metadata = result.get("metadata", {})
                # Ajouter le score du re-ranker si disponible
                if "reranker_score" in result:
                    source.metadata["reranker_score"] = result["reranker_score"]
                    source.metadata["original_score"] = result.get("original_score", 0.0)
                
                sources.append(source)
            
            # Appliquer des filtres contextuels
            filtered_sources = await self._filter_sources_by_context(sources, context_type, question)
            
            # Limiter au nombre demandé
            return filtered_sources[:max_sources]
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche sources: {e}")
            return []
    
    async def _filter_sources_by_context(self, sources: List[DocumentSource], 
                                       context_type: str, question: str) -> List[DocumentSource]:
        """
        Filtre les sources selon le type de contexte demandé
        
        Args:
            sources: Liste des sources trouvées
            context_type: Type de contexte
            question: Question originale
            
        Returns:
            Sources filtrées et réordonnées
        """
        if context_type == "general":
            return sources
        
        # Mots-clés par contexte pour améliorer la pertinence
        context_keywords = {
            "particulier": ["revenus", "déclaration", "impôt sur le revenu", "déduction", "crédit d'impôt", "foyer fiscal", "particulier", "personne physique"],
            "entreprise": ["bénéfices", "TVA", "IS", "impôt sur les sociétés", "déduction", "amortissement", "charges", "entreprise", "société", "commercial"],
            "fiscal": ["taux", "barème", "calcul", "assiette", "exonération", "régime fiscal", "impôt", "taxe", "fiscal", "fiscale"]
        }
        
        keywords = context_keywords.get(context_type, [])
        
        # Re-scorer les sources selon le contexte
        for source in sources:
            context_bonus = 0.0
            content_lower = source.content.lower()
            
            for keyword in keywords:
                if keyword in content_lower:
                    context_bonus += 0.1
            
            # Bonus si le contexte apparaît dans le titre/section
            if context_type in source.title.lower() or context_type in source.section.lower():
                context_bonus += 0.2
            
            source.relevance_score += context_bonus
        
        # Re-trier par score
        sources.sort(key=lambda s: s.relevance_score, reverse=True)
        return sources
    
    async def generate_response_stream(self, question: str, 
                                     sources: List[DocumentSource],
                                     temperature: float = 0.3,
                                     max_tokens: int = 1000,
                                     personnalite: str = "expert_cgi") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Génère une réponse streamée basée sur les sources trouvées
        
        Args:
            question: Question de l'utilisateur
            sources: Sources pertinentes trouvées
            temperature: Température pour la génération (0.0 à 1.0)
            max_tokens: Nombre maximum de tokens à générer
            
        Yields:
            Chunks de réponse avec métadonnées
        """
        try:
            # Vérifier que le service LLM est disponible
            if not self.llm_service:
                yield {"error": "Service LLM Gemini non disponible", "complete": True}
                return
            
            # Construire le contexte à partir des sources
            context = self._build_context_from_sources(sources)
            
            # Créer le prompt système
            system_prompt = self._create_system_prompt()
            
            # Utiliser directement le service Gemini
            async for chunk in self.llm_service.generate_response_stream(
                prompt=question,
                context_documents=[{"content": context, "source": "CGI_Benin", "score": 1.0}],
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                personnalite=personnalite
            ):
                yield chunk
                    
        except Exception as e:
            logger.error(f"❌ Erreur génération réponse: {e}")
            yield {"error": f"Erreur lors de la génération: {str(e)}", "complete": True}
    
    def _build_context_from_sources(self, sources: List[DocumentSource]) -> str:
        """Construit le contexte textuel à partir des sources"""
        if not sources:
            return "Aucune source pertinente trouvée dans le Code Général des Impôts."
        
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_part = f"""
--- SOURCE {i} ---
Titre: {source.title}
Section: {source.section}
Article: {source.article}
Fichier: {os.path.basename(source.source_file)}

Contenu:
{source.content}

Score de pertinence: {source.relevance_score:.2f}
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _generate_simple_response(self, question: str, sources: List[DocumentSource]) -> str:
        """Génère une réponse simple basée sur les sources trouvées"""
        try:
            if not sources:
                return "Je n'ai pas trouvé d'informations pertinentes dans le Code Général des Impôts pour répondre à votre question."
            
            # Extraire le contenu des sources
            source_contents = []
            for source in sources:
                content = source.content
                if content and len(content) > 50:
                    # Nettoyer le contenu
                    clean_content = content.replace('\n', ' ').replace('  ', ' ').strip()
                    source_contents.append(clean_content[:400])  # Limiter la longueur
            
            if not source_contents:
                return "Les sources trouvées ne contiennent pas d'informations suffisantes pour répondre à votre question."
            
            # Construire la réponse
            response_parts = []
            response_parts.append(f"Basé sur l'analyse du Code Général des Impôts du Bénin, voici ce que j'ai trouvé concernant votre question :")
            response_parts.append("")
            
            # Ajouter des extraits des sources les plus pertinentes
            for i, content in enumerate(source_contents[:3], 1):
                response_parts.append(f"**Source {i} :**")
                response_parts.append(content)
                response_parts.append("")
            
            response_parts.append("**Note :** Cette réponse est basée sur l'analyse automatique des documents CGI. Pour des informations juridiques précises et à jour, consultez un professionnel du droit ou l'administration fiscale.")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Erreur génération réponse simple: {str(e)}")
            return "Je ne peux pas générer de réponse pour le moment. Veuillez reformuler votre question."
    
    def _create_system_prompt(self) -> str:
        """Crée le prompt système pour le LLM"""
        return """Tu es un assistant expert en droit fiscal béninois, spécialisé dans le Code Général des Impôts (CGI) du Bénin.

IMPORTANT: Tu traites UNIQUEMENT du Code Général des Impôts de la République du Bénin, pas de la France ni d'autres pays.

Tes responsabilités:
- Fournir des réponses précises basées sur les textes du CGI
- Citer les références légales appropriées (articles, sections)
- Expliquer les concepts fiscaux de manière claire
- Distinguer entre différents types de contribuables (particuliers, entreprises)
- Indiquer les limitations de tes connaissances

Style de réponse:
- Professionnel mais accessible
- Structuré avec des sections claires
- Citations précises des articles
- Exemples pratiques quand approprié
- Prudence juridique (recommander de consulter un expert si nécessaire)

Important: Base-toi UNIQUEMENT sur le contexte fourni. Si une information n'est pas présente dans le contexte, dis-le explicitement."""

    def calculate_confidence(self, question: str, sources: List[DocumentSource], 
                           response: str) -> float:
        """
        Calcule un score de confiance pour la réponse générée
        
        Args:
            question: Question originale
            sources: Sources utilisées
            response: Réponse générée
            
        Returns:
            Score de confiance entre 0 et 1
        """
        if not sources:
            return 0.0
        
        try:
            # Facteurs de confiance
            factors = []
            
            # 1. Qualité des sources (score de pertinence moyen)
            avg_relevance = sum(s.relevance_score for s in sources) / len(sources)
            factors.append(min(avg_relevance, 1.0))
            
            # 2. Nombre de sources
            source_factor = min(len(sources) / 3.0, 1.0)  # Optimal autour de 3 sources
            factors.append(source_factor)
            
            # 3. Longueur de réponse (ni trop courte ni trop longue)
            response_length = len(response.split())
            if response_length < 20:
                length_factor = 0.3
            elif response_length > 500:
                length_factor = 0.7
            else:
                length_factor = 1.0
            factors.append(length_factor)
            
            # 4. Présence de références juridiques dans la réponse
            legal_refs = ["article", "section", "CGI", "alinéa", "paragraphe"]
            ref_count = sum(1 for ref in legal_refs if ref.lower() in response.lower())
            ref_factor = min(ref_count / 2.0, 1.0)
            factors.append(ref_factor)
            
            # Calcul final (moyenne pondérée)
            weights = [0.4, 0.2, 0.2, 0.2]  # Importance des facteurs
            confidence = sum(f * w for f, w in zip(factors, weights))
            
            return round(confidence, 3)
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul confiance: {e}")
            return 0.5
    
    async def save_query_log(self, query_id: str, question: str, 
                           response: str, metadata: Dict[str, Any]):
        """Sauvegarde le log d'une requête pour analytics"""
        log_entry = {
            "query_id": query_id,
            "question": question,
            "response_length": len(response),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        self.query_logs.append(log_entry)
        
        # Garder seulement les 1000 derniers logs
        if len(self.query_logs) > 1000:
            self.query_logs = self.query_logs[-1000:]
    
    async def is_indexed(self) -> bool:
        """Vérifie si des documents sont déjà indexés"""
        if not self.is_initialized:
            return False
        return await self.vector_store.has_documents()
    
    async def get_documents_count(self) -> int:
        """Retourne le nombre de documents indexés"""
        if not self.is_initialized:
            return 0
        return await self.vector_store.get_document_count()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service RAG"""
        if not self.is_initialized:
            return {"error": "Service non initialisé"}
        
        return {
            "documents_indexed": await self.get_documents_count(),
            "queries_processed": len(self.query_logs),
            "embedding_cache_size": len(self.embedding_service.embedding_cache),
            "current_model": self.llm_service.get_current_model_info(),
            "embedding_info": self.embedding_service.get_model_info(),
            "vector_store_stats": await self.vector_store.get_stats(),
            "recent_queries": self.query_logs[-10:] if self.query_logs else []
        }
    
    async def reindex_documents(self, documents_path: str):
        """Réindexe complètement les documents"""
        logger.info("🔄 Début de la réindexation...")
        
        # Vider la base vectorielle
        await self.vector_store.clear()
        
        # Vider les caches
        await self.embedding_service.clear_cache()
        self.query_cache.clear()
        
        # Réindexer
        await self.index_documents(documents_path)
        
        logger.info("✅ Réindexation terminée")
    
    async def cleanup(self):
        """Nettoyage des ressources"""
        logger.info("🧹 Nettoyage du service RAG...")
        
        if hasattr(self.vector_store, 'cleanup'):
            await self.vector_store.cleanup()
        
        # Nettoyer le re-ranker
        if hasattr(self.reranker_service, 'cleanup'):
            await self.reranker_service.cleanup()
        
        # Sauvegarder les logs si nécessaire
        if self.query_logs:
            log_file = f"query_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(self.query_logs, f, indent=2, ensure_ascii=False)
                logger.info(f"📝 Logs sauvegardés dans {log_file}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur sauvegarde logs: {e}")
        
        logger.info("✅ Nettoyage terminé")