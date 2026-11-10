# Explainable Multi-Agent AI Framework for Intelligent Data Quality Monitoring and Adaptive Auto-Correction

An enterprise-grade, multi-agent AI system designed for automated data profiling, adaptive anomaly detection, explainable remediation, audit tracking, and executive PDF reporting.

---

## 🌟 Key Capabilities

1. **Multi-Agent Coordination Architecture**:
   - **Dynamic Profiler Agent**: Computes statistical summaries, data type distributions, cardinality, and completeness metrics.
   - **Adaptive Anomaly Detection Engine**: Employs Isolation Forests, Local Outlier Factor (LOF), and statistical thresholds to isolate subtle inconsistencies.
   - **Remediation & Auto-Correction Engine**: Applies rule-based, statistical, and ML imputations/standardizations while preserving data integrity.
   - **Explainable AI (XAI) Service**: Yields interpretable feature-importance rankings, SHAP-aligned contributions, and actionable reasoning behind flagged issues.
   - **Generated Code Agent**: Converts natural language data transformation requests into executable, reproducible Python/Pandas scripts.
   - **RAG Chatbot Service**: Empowers users to query dataset quality, anomalies, and schema semantics in natural language.

2. **Enterprise Governance & Security**:
   - **Multi-Tenant Data Isolation**: Strict tenant scoping (`org_id`) across disk storage and database records.
   - **Role-Based Access Control (RBAC)**: Admin, Data Engineer, and Viewer authorization profiles.
   - **Automated PII Masking**: Detection and redaction of sensitive identifiers (emails, phone numbers, credit card numbers, SSNs).
   - **File & Path Traversal Guards**: Strict MIME and magic byte validation for CSV, Excel, Parquet, and JSON uploads.
   - **Google OAuth 2.0 & JWT Authentication**: Support for single sign-on alongside local credential management.

3. **Audit Trails & Executive Reporting**:
   - **Interactive Before/After Comparison Suite**: Visual side-by-side assessment of quality distributions and dimension metrics.
   - **Executive PDF Audit Reports**: Multi-page ISO/IEC 25012-aligned reports with radar quality charts, distribution plots, and cryptographic hashes.

---

## 🏗️ Project Architecture

```
code/
├── frontend/                          # ReactJS 18 Frontend (Vite, TailwindCSS, Chart.js)
│   ├── src/components/                # Reusable UI widgets & report modals
│   ├── src/pages/                     # Upload, Profiling, Anomalies, Corrections, Explainability, Chat
│   └── src/context/                   # Global Auth and Dataset state providers
├── backend/                           # FastAPI Multi-Agent Asynchronous Backend
│   ├── api/                           # REST routers (auth, upload, reports, chat, explainability)
│   ├── core/                          # Config, SQLite engine, RBAC, file security, tenant isolation
│   ├── models/                        # SQLAlchemy ORM schemas
│   ├── services/agents/               # Multi-agent engines (dynamic analyzer, remediator, anomaly)
│   ├── services/ai/                   # Explainable AI (XAI) service
│   ├── services/exporter/             # Enterprise multi-page PDF generation engine
│   ├── services/reports/              # Chart generators, content builders, profiling services
│   ├── services/storage/              # Multi-tenant Parquet/CSV dataset & code persistence
│   └── tests/                         # Pytest end-to-end and unit test suite
├── database/                          # SQLite store (`data_quality.db`) and Alembic migrations
├── datasets/                          # Seed and benchmark datasets
└── docs/                              # Architecture, API endpoints, workflows, diagrams
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (Recommended: Python 3.11)
- Node.js 18+ and npm
- Git

### 1. Unified Launcher (Recommended)
Run both backend (FastAPI on `:8000`) and frontend (Vite on `:3000`/`:5173`) using the unified launcher:

```bash
python app.py
```

### 2. Manual Launch in Separate Terminals

#### Terminal 1 — Backend
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Terminal 2 — Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Verification

Run the comprehensive Pytest verification suite:

```bash
pytest backend/tests
```

Build and verify the frontend bundle:

```bash
cd frontend
npm run build
```

---

## 🔒 Configuration & Environment Variables

Copy `.env.example` to `.env` in the project root and configure:

```env
SECRET_KEY=your_secure_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./database/data_quality.db

# Multi-Tenancy & Uploads
UPLOAD_DIR=./uploads
CLEANED_DIR=./cleaned_datasets

# Optional OAuth 2.0
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/oauth/callback
```
