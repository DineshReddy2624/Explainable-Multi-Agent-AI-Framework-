from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging

from core.database import get_db
from core.tenant_security import get_tenant_context, verify_dataset_access
from core.response import StandardResponse
from services.storage.dataset_storage_service import storage_service
from services.ai.llm_provider import LLMFactory

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{dataset_id}")
def get_anomalies(dataset_id: int, db: Session = Depends(get_db), tenant: dict = Depends(get_tenant_context)):
    verify_dataset_access(dataset_id, tenant["org_id"], db)
    loaded = storage_service.load_dataset(dataset_id, db=db, org_id=tenant["org_id"])
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")

    analysis = loaded.get("analysis", {})
    anomalies = analysis.get("anomalies", [])
    data = {
        "dataset_id": dataset_id,
        "model": "Adaptive Anomaly Engine (Isolation Forest, LOF, Z-Score)",
        "total_anomalies": len(anomalies),
        "anomalies": anomalies
    }
    return StandardResponse.ok(data=data, message="Fetched anomaly detection results")


# -----------------------------------------------------------------
# LLM-powered outlier explanation endpoint
# -----------------------------------------------------------------
class ExplainRequest(BaseModel):
    row_index: int
    column: str
    value: Any
    anomaly_score: float
    reason: Optional[str] = None
    row_data: Optional[Dict[str, Any]] = None


@router.post("/explain")
def explain_outlier(body: ExplainRequest):
    """
    Generate a rich, LLM-powered natural-language explanation for a detected
    data outlier / anomaly using the configured LLM (Groq preferred).
    """
    # Build a concise context prompt
    row_summary = ""
    if body.row_data:
        pairs = [f"  - {k}: {v}" for k, v in body.row_data.items()]
        row_summary = "\n".join(pairs[:15])  # limit to 15 fields

    system_prompt = (
        "You are an expert Data Quality Analyst specializing in outlier detection and data profiling. "
        "Your task is to explain, in plain business English (2-4 sentences), WHY a specific value has been "
        "flagged as an outlier by an ML Isolation Forest / Z-Score algorithm. "
        "Be specific, reference the actual value and column name, and explain the real-world risk or data "
        "quality implication. Keep it concise — no bullet points, no markdown, just clear readable prose."
    )

    user_prompt = (
        f"A data quality anomaly has been detected in the dataset.\n\n"
        f"**Column:** {body.column}\n"
        f"**Outlier Value:** {body.value}\n"
        f"**Anomaly Score:** {body.anomaly_score:.2f} (scale: 0-1, higher = more anomalous)\n"
        f"**Row Index:** #{body.row_index + 1}\n"
        f"**Statistical Reason:** {body.reason or 'Flagged as statistical outlier via Z-Score / Isolation Forest.'}\n\n"
        f"**Full Row Context:**\n{row_summary}\n\n"
        f"Explain clearly why this value is anomalous, what it means for data quality, and what could have caused it."
    )

    try:
        llm = LLMFactory.get_provider()
        response = llm.generate(prompt=user_prompt, system_prompt=system_prompt, temperature=0.7)
        explanation = response.content.strip()
        provider = response.provider
    except Exception as e:
        logger.warning(f"LLM explain failed, falling back to template reason. Error: {e}")
        # Smart fallback: build a detailed template-based explanation
        score_pct = int(body.anomaly_score * 100)
        explanation = (
            f"The value '{body.value}' in column '{body.column}' (Row #{body.row_index + 1}) "
            f"has been flagged with an anomaly confidence of {score_pct}%. "
            f"This value deviates significantly from the statistical distribution of the column — "
            f"it lies outside the expected range based on Z-Score analysis (threshold: ±2.8 standard deviations). "
            f"Such values can indicate data entry errors, sensor malfunctions, or fraudulent records "
            f"and should be reviewed before using this dataset for machine learning or reporting."
        )
        provider = "template"

    return StandardResponse.ok(data={
        "explanation": explanation,
        "provider": provider,
        "column": body.column,
        "value": body.value,
        "row_index": body.row_index
    }, message="Outlier explanation generated")
