import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.services.rag_service import RAGService
from app.models.schemas import QueryRequest, QueryResponse, HealthResponse
from app.utils.markdown_parser import MarkdownParser

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instance globale du service RAG
rag_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    global rag_service
    
    logger.info("🚀 Démarrage du serveur RAG CGI")
    
    # Initialiser le service RAG
    rag_service = RAGService()
    await rag_service.initialize()
    
    # Vérifier si les documents sont déjà indexés
    if not await rag_service.is_indexed():
        logger.info("📚 Indexation des documents CGI en cours...")
        await rag_service.index_documents("./data/cgi_documents")
        logger.info("✅ Indexation terminée")
    
    yield
    
    # Nettoyage
    logger.info("🛑 Arrêt du serveur")
    if rag_service:
        await rag_service.cleanup()

# Application FastAPI
app = FastAPI(
    title="RAG CGI avec Server-Sent Events",
    description="API de recherche dans le Code Général des Impôts avec streaming en temps réel",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==============================================================================
# ENDPOINTS API
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def get_interface():
    """Interface de test pour le RAG"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG CGI - Test Interface</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .input-section, .output-section { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
            textarea { width: 100%; height: 150px; margin: 10px 0; padding: 10px; border-radius: 4px; border: 1px solid #ccc; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .response { background: #f8f9fa; padding: 15px; border-radius: 4px; min-height: 300px; overflow-y: auto; white-space: pre-wrap; }
            .sources { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 4px; }
            .source-item { margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }
            .loading { color: #007bff; font-style: italic; }
            .error { color: #dc3545; }
            .success { color: #28a745; }
        </style>
    </head>
    <body>
        <h1>🏛️ RAG Code Général des Impôts</h1>
        <p>Interface de test pour interroger le CGI en temps réel avec Server-Sent Events</p>
        
        <div class="container">
            <div class="input-section">
                <h3>📝 Votre Question</h3>
                <textarea id="question" placeholder="Ex: Quels sont les taux d'imposition sur les revenus locatifs ?"></textarea>
                
                <h4>Paramètres</h4>
                <label>Type de contexte:</label>
                <select id="context_type">
                    <option value="general">Général</option>
                    <option value="particulier">Particulier</option>
                    <option value="entreprise">Entreprise</option>
                    <option value="fiscal">Fiscal</option>
                </select>
                
                <br><br>
                <label>Personnalité du chatbot:</label>
                <select id="personnalite">
                    <option value="expert">🧠 Expert - Réponses courtes</option>
                    <option value="expert_cgi" selected>🏛️ Expert CGI - Réponses détaillées</option>
                    <option value="mathematicien">🧮 Mathématicien - Formules KaTeX</option>
                </select>
                
                <br><br>
                <label>Nombre de sources max:</label>
                <input type="number" id="max_sources" value="3" min="1" max="10">
                
                <br><br>
                <button id="askButton" onclick="askQuestion()">🚀 Poser la Question</button>
                <button id="stopButton" onclick="stopStream()" disabled>⏹️ Arrêter</button>
            </div>
            
            <div class="output-section">
                <h3>🤖 Réponse en Temps Réel</h3>
                <div id="response" class="response"></div>
                
                <div id="sources" class="sources" style="display: none;">
                    <h4>📚 Sources utilisées</h4>
                    <div id="sources-list"></div>
                </div>
                
                <div id="metadata" style="margin-top: 15px; font-size: 0.9em; color: #666;"></div>
            </div>
        </div>

        <script>
            let eventSource = null;
            let currentResponse = '';

            async function askQuestion() {
                const question = document.getElementById('question').value.trim();
                if (!question) {
                    alert('Veuillez saisir une question');
                    return;
                }

                // Reset UI
                document.getElementById('response').innerHTML = '<div class="loading">🔄 Recherche en cours...</div>';
                document.getElementById('sources').style.display = 'none';
                document.getElementById('metadata').innerHTML = '';
                document.getElementById('askButton').disabled = true;
                document.getElementById('stopButton').disabled = false;
                currentResponse = '';

                // Paramètres
                const contextType = document.getElementById('context_type').value;
                const maxSources = document.getElementById('max_sources').value;
                const personnalite = document.getElementById('personnalite').value;

                // URL avec paramètres
                const url = `/query/stream?question=${encodeURIComponent(question)}&context_type=${contextType}&max_sources=${maxSources}&personnalite=${personnalite}`;

                // Créer EventSource
                eventSource = new EventSource(url);

                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleStreamData(data);
                };

                eventSource.onerror = function(event) {
                    console.error('Erreur SSE:', event);
                    document.getElementById('response').innerHTML = '<div class="error">❌ Erreur de connexion</div>';
                    stopStream();
                };
            }

            function handleStreamData(data) {
                const responseDiv = document.getElementById('response');
                
                if (data.type === 'search_start') {
                    responseDiv.innerHTML = '<div class="loading">🔍 Recherche dans les documents CGI...</div>';
                } else if (data.type === 'sources_found') {
                    responseDiv.innerHTML = '<div class="loading">📚 ' + data.count + ' sources trouvées. Génération de la réponse...</div>';
                    displaySources(data.sources);
                } else if (data.type === 'response_start') {
                    responseDiv.innerHTML = '';
                    currentResponse = '';
                } else if (data.type === 'response_chunk') {
                    currentResponse += data.content;
                    responseDiv.innerHTML = currentResponse;
                } else if (data.type === 'response_complete') {
                    displayMetadata(data.metadata);
                    stopStream();
                } else if (data.type === 'error') {
                    responseDiv.innerHTML = '<div class="error">❌ ' + data.message + '</div>';
                    stopStream();
                }
            }

            function displaySources(sources) {
                const sourcesDiv = document.getElementById('sources');
                const sourcesList = document.getElementById('sources-list');
                
                sourcesList.innerHTML = sources.map((source, index) => `
                    <div class="source-item">
                        <strong>📄 ${source.title}</strong><br>
                        <em>Section: ${source.section}</em><br>
                        <small>${source.content.substring(0, 200)}...</small>
                    </div>
                `).join('');
                
                sourcesDiv.style.display = 'block';
            }

            function displayMetadata(metadata) {
                document.getElementById('metadata').innerHTML = `
                    ⏱️ Temps de traitement: ${metadata.processing_time}s | 
                    🎯 Score de confiance: ${Math.round(metadata.confidence * 100)}% |
                    🔤 Tokens utilisés: ${metadata.tokens_used}
                `;
            }

            function stopStream() {
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                document.getElementById('askButton').disabled = false;
                document.getElementById('stopButton').disabled = true;
            }

            // Exemple de questions prédéfinies
            function setExample(question) {
                document.getElementById('question').value = question;
            }

            // Ajouter des exemples
            document.addEventListener('DOMContentLoaded', function() {
                const examples = document.createElement('div');
                examples.innerHTML = `
                    <h4>💡 Questions d'exemple:</h4>
                    <button onclick="setExample('Quels sont les taux d\\'imposition sur les revenus locatifs ?')" style="margin:5px; padding:5px 10px; font-size:12px;">Revenus locatifs</button>
                    <button onclick="setExample('Comment déclarer une plus-value immobilière ?')" style="margin:5px; padding:5px 10px; font-size:12px;">Plus-value immobilière</button>
                    <button onclick="setExample('Quelles sont les déductions possibles pour un auto-entrepreneur ?')" style="margin:5px; padding:5px 10px; font-size:12px;">Auto-entrepreneur</button>
                `;
                document.querySelector('.input-section').appendChild(examples);
            });
        </script>
    </body>
    </html>
    """

@app.get("/query/stream")
async def stream_query(
    question: str = Query(..., description="Question à poser au CGI"),
    context_type: str = Query("general", description="Type de contexte"),
    max_sources: int = Query(3, ge=1, le=10, description="Nombre max de sources"),
    personnalite: str = Query("expert_cgi", description="Personnalité du chatbot")
):
    """Endpoint de streaming pour les requêtes RAG"""
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="Service RAG non initialisé")
    
    async def generate_stream():
        try:
            query_id = str(uuid.uuid4())
            start_time = time.time()
            
            # 1. Recherche des sources
            yield f"data: {json.dumps({'type': 'search_start', 'query_id': query_id})}\n\n"
            
            sources = await rag_service.search_relevant_sources(
                question, max_sources, context_type
            )
            
            yield f"data: {json.dumps({'type': 'sources_found', 'count': len(sources), 'sources': [s.to_dict() for s in sources]})}\n\n"
            
            # 2. Génération de la réponse streamée
            yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
            
            response_content = ""
            tokens_used = 0
            
            async for chunk in rag_service.generate_response_stream(
                question, 
                sources, 
                temperature=0.3, 
                max_tokens=1000, 
                personnalite=personnalite
            ):
                if chunk.get('content'):
                    response_content += chunk['content']
                    tokens_used += chunk.get('tokens', 0)
                    
                    yield f"data: {json.dumps({'type': 'response_chunk', 'content': chunk['content']})}\n\n"
            
            # 3. Finalisation
            processing_time = time.time() - start_time
            confidence = rag_service.calculate_confidence(question, sources, response_content)
            
            metadata = {
                'processing_time': round(processing_time, 2),
                'confidence': confidence,
                'tokens_used': tokens_used,
                'sources_count': len(sources)
            }
            
            yield f"data: {json.dumps({'type': 'response_complete', 'metadata': metadata})}\n\n"
            
            # Sauvegarder la requête pour analytics
            await rag_service.save_query_log(query_id, question, response_content, metadata)
            
        except Exception as e:
            logger.error(f"Erreur durant le streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.post("/query", response_model=QueryResponse)
async def query_cgi(request: QueryRequest):
    """Endpoint classique (non-streaming) pour compatibilité"""
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="Service RAG non initialisé")
    
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    try:
        # Recherche des sources
        sources = await rag_service.search_relevant_sources(
            request.question, request.max_sources, request.context_type
        )
        
        # Génération de la réponse
        response_content = ""
        tokens_used = 0
        
        async for chunk in rag_service.generate_response_stream(
            request.question, 
            sources, 
            request.temperature, 
            1000, 
            request.personnalite
        ):
            if chunk.get('content'):
                response_content += chunk['content']
                tokens_used += chunk.get('tokens', 0)
        
        processing_time = time.time() - start_time
        confidence = rag_service.calculate_confidence(request.question, sources, response_content)
        
        return QueryResponse(
            success=True,
            answer=response_content,
            sources=[s.to_dict() for s in sources],
            confidence_score=confidence,
            query_id=query_id,
            processing_time=processing_time,
            tokens_used=tokens_used
        )
        
    except Exception as e:
        logger.error(f"Erreur traitement requête: {e}")
        return QueryResponse(
            success=False,
            answer=f"Erreur: {str(e)}",
            sources=[],
            confidence_score=0.0,
            query_id=query_id,
            processing_time=time.time() - start_time,
            tokens_used=0
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check de l'API"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "rag_service": "initialized" if rag_service else "not_initialized",
        "documents_indexed": await rag_service.get_documents_count() if rag_service else 0
    }
    
    return HealthResponse(**health_status)

@app.get("/stats")
async def get_stats():
    """Statistiques du service RAG"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="Service RAG non initialisé")
    
    return await rag_service.get_stats()

@app.get("/personnalites")
async def get_personnalites():
    """Informations sur les personnalités disponibles du chatbot"""
    try:
        from app.services.personnalite_service import PersonnaliteService
        personnalite_service = PersonnaliteService()
        return personnalite_service.get_personnalite_info()
    except ImportError:
        return {
            "error": "Service de personnalités non disponible",
            "personnalites": {
                "expert": "Expert Fiscal - Réponses courtes",
                "expert_cgi": "Expert CGI - Réponses détaillées",
                "mathematicien": "Mathématicien - Formules mathématiques"
            }
        }

@app.post("/reindex")
async def reindex_documents():
    """Réindexer les documents CGI"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="Service RAG non initialisé")
    
    try:
        await rag_service.reindex_documents("./data/cgi_documents")
        return {"message": "Réindexation terminée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur réindexation: {str(e)}")

# ==============================================================================
# DÉMARRAGE DE L'APPLICATION
# ==============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )