# REST API Documentation

## Auth Endpoints (`/api/v1/auth`)
- `POST /login` - Authenticate user & issue JWT token.
- `POST /register` - Register a new user account.
- `GET /me` - Get current authenticated user details.

## Dataset Endpoints (`/api/v1/upload`)
- `POST /upload` - Upload raw CSV/Excel dataset file.
- `GET /datasets` - List uploaded datasets.
- `GET /datasets/{id}` - Fetch dataset details and metadata.

## Data Profiling (`/api/v1/profiling`)
- `POST /profile/{dataset_id}` - Trigger automated profiling agent run.
- `GET /profile/{dataset_id}` - Retrieve detailed profiling metrics and summary.

## Data Issues (`/api/v1/issues`)
- `GET /issues/{dataset_id}` - List detected missing values, duplicates, format mismatches, and anomalies.

## Monitoring & Tracking (`/api/v1/monitoring`)
- `GET /metrics/{dataset_id}` - Get real-time data quality scores and health status.
- `GET /timeline/{dataset_id}` - Fetch audit logs and processing activity.

## Auto-Correction (`/api/v1/correction`)
- `POST /suggest/{dataset_id}` - Generate AI-assisted remediation recommendations.
- `POST /apply/{dataset_id}` - Execute auto-corrections and output cleaned dataset.

## Explainability (`/api/v1/explainability`)
- `GET /shap/{dataset_id}` - Return feature importance and SHAP explanation data.

## Chatbot RAG (`/api/v1/chatbot`)
- `POST /query` - Ask natural language questions against uploaded dataset vector store.

## Rules Engine (`/api/v1/rules`)
- `POST /rules` - Create custom data quality validation rules.
- `POST /rules/execute/{dataset_id}` - Run custom rules engine against dataset.

## Export & Reports (`/api/v1/reports` & `/api/v1/export`)
- `GET /reports/{dataset_id}/download` - Download PDF / CSV / JSON data quality reports.
