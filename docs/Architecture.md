# Architecture Documentation

## System Overview

The AI-Powered Data Quality & Profiling Platform is built using a decoupled Multi-Agent System architecture:

```
[ Frontend: ReactJS + Vite ]
         │ (REST API / JSON)
         ▼
[ FastAPI Backend Gateway & Controller ]
         │
    ┌────┴───────────────────────────┐
    ▼                                ▼
[ Agent Coordinator ]       [ RAG Chatbot Service ]
    │                                │
    ├─► Profiling Agent              ├─► Metadata / CSV Loader
    ├─► Missing Value Agent          ├─► Vector Embeddings Store
    ├─► Duplicate Detection Agent    └─► LLM RAG Pipeline
    ├─► Format Validation Agent
    ├─► Anomaly Agent (IF/LOF/DBSCAN)
    ├─► Quality Score Agent
    ├─► Auto-Correction Agent
    ├─► SHAP Explainability Agent
    └─► Rule Engine Agent
         │
         ▼
[ Database & Persistence ]
 (SQLite / SQLAlchemy / FAISS)
```

## Core Layers
1. **Presentation Layer (ReactJS)**: Interactive UI components, dashboard visualizations, monitoring tables, and RAG chat view.
2. **API Layer (FastAPI)**: Lightweight, asynchronous API routing with Pydantic payload validation.
3. **Agentic Coordination Layer**: Orchestrates specialized ML & statistical analysis sub-agents.
4. **Data & Storage Layer**: SQLite ORM database for metadata, FAISS/Chroma for vector embeddings, disk storage for datasets & reports.
