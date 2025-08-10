# 🚀 RAG CGI avec Server-Sent Events - Architecture Complète


# Structure du projet :
rag-cgi-project/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app principale
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Modèles Pydantic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_service.py      # Logique RAG
│   │   ├── embedding_service.py # Gestion embeddings
│   │   └── llm_service.py      # Interface OpenAI
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── markdown_parser.py  # Parser documents CGI
│   │   └── text_splitter.py    # Chunking intelligent
│   └── database/
│       ├── __init__.py
│       └── vector_store.py     # ChromaDB interface
├── data/
│   └── cgi_documents/          # Documents Markdown CGI
├── static/
│   ├── index.html              # Interface de test
│   └── style.css
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
