from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=2000, description="Question à poser")
    context_type: str = Field("general", pattern="^(general|particulier|entreprise|fiscal)$")
    max_sources: int = Field(3, ge=1, le=10, description="Nombre max de sources")
    temperature: float = Field(0.3, ge=0.0, le=1.0, description="Créativité de la réponse")

class SourceInfo(BaseModel):
    title: str
    section: str
    article: str
    content: str
    relevance_score: float
    source_file: str

class QueryResponse(BaseModel):
    success: bool
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    query_id: str
    processing_time: float
    tokens_used: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    rag_service: str
    documents_indexed: int
