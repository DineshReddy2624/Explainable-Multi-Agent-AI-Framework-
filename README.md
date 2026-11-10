# AI-Powered Data Quality & Profiling Platform

An enterprise-grade, multi-agent AI data quality profiling, monitoring, auto-correction, and RAG-powered data intelligence system.

## Project Architecture

```
code/
├── frontend/                          # ReactJS Frontend (Vite)
├── backend/                           # FastAPI Multi-Agent Backend
├── database/                          # SQLite & Migrations
├── datasets/                          # Original & Cleaned Data Storage
├── docs/                              # API, Architecture & Workflow Documentation
└── tests/                             # Backend & Frontend Test Suites
```

## Quick Start

### Option 1: Run Both Backend & Frontend with One Command (Recommended)

Run `app.py` from the root directory:

```bash
python app.py
```

*This will automatically launch the FastAPI Backend (Port 8000), wait for it to become ready, and then launch the React Frontend dev server.*

---

### Option 2: Run Separately in Two Terminals

#### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

