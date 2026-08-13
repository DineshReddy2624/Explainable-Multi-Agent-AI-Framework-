import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.celery_app import celery_app
from models.job import Job
from services.storage.dataset_storage_service import storage_service
from services.agents.dynamic_analyzer import DynamicDatasetAnalyzer
from services.agents.adaptive_anomaly_engine import AdaptiveAnomalyEngine
from services.agents.dynamic_remediator import DynamicDatasetRemediator

analyzer = DynamicDatasetAnalyzer()
anomaly_engine = AdaptiveAnomalyEngine()
remediator = DynamicDatasetRemediator()

def _update_job_status(job_id: str, status: str, progress: int = 0, result_data: Optional[Dict[str, Any]] = None, error_msg: Optional[str] = None):
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = status
            job.progress = progress
            if status == "RUNNING" and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ["SUCCESS", "FAILED"]:
                job.completed_at = datetime.utcnow()
                if progress == 0 and status == "SUCCESS":
                    job.progress = 100
            if result_data is not None:
                job.result_data = result_data
            if error_msg:
                job.error_message = error_msg
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def profile_dataset_task(self, dataset_id: int, job_id: str):
    _update_job_status(job_id, "RUNNING", progress=20)
    db: Session = SessionLocal()
    try:
        dataset_data = storage_service.load_dataset(dataset_id, db=db)
        if not dataset_data:
            raise ValueError(f"Dataset #{dataset_id} not found in persistent storage.")

        df = dataset_data["cleaned_df"] if "cleaned_df" in dataset_data else dataset_data["raw_df"]
        filename = dataset_data.get("filename", f"dataset_{dataset_id}.csv")

        _update_job_status(job_id, "RUNNING", progress=60)
        analysis_result = analyzer.analyze(df, filename)

        payload = {
            "dataset_id": dataset_id,
            "filename": filename,
            "analysis": analysis_result
        }
        _update_job_status(job_id, "SUCCESS", progress=100, result_data=payload)
        return payload
    except Exception as exc:
        _update_job_status(job_id, "FAILED", error_msg=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            pass
        raise exc
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def anomaly_detection_task(self, dataset_id: int, job_id: str):
    _update_job_status(job_id, "RUNNING", progress=20)
    db: Session = SessionLocal()
    try:
        dataset_data = storage_service.load_dataset(dataset_id, db=db)
        if not dataset_data:
            raise ValueError(f"Dataset #{dataset_id} not found in persistent storage.")

        df = dataset_data.get("cleaned_df", dataset_data.get("raw_df"))
        
        _update_job_status(job_id, "RUNNING", progress=50)
        anomaly_results = anomaly_engine.detect_anomalies(df)

        payload = {
            "dataset_id": dataset_id,
            "model": "Isolation Forest + Z-Score Hybrid",
            "anomaly_results": anomaly_results
        }
        _update_job_status(job_id, "SUCCESS", progress=100, result_data=payload)
        return payload
    except Exception as exc:
        _update_job_status(job_id, "FAILED", error_msg=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            pass
        raise exc
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def apply_corrections_task(self, dataset_id: int, cell_edits: List[Any], strategies: List[Any], job_id: str):
    _update_job_status(job_id, "RUNNING", progress=20)
    db: Session = SessionLocal()
    try:
        dataset_data = storage_service.load_dataset(dataset_id, db=db)
        if not dataset_data:
            raise ValueError(f"Dataset #{dataset_id} not found in persistent storage.")

        current_df = dataset_data["raw_df"].copy()
        _update_job_status(job_id, "RUNNING", progress=50)

        cleaned_df, logs = remediator.apply_remediation(current_df, cell_edits, strategies)
        result_data = storage_service.save_cleaned_dataset(dataset_id, cleaned_df, logs, db=db)

        _update_job_status(job_id, "SUCCESS", progress=100, result_data=result_data)
        return result_data
    except Exception as exc:
        _update_job_status(job_id, "FAILED", error_msg=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            pass
        raise exc
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def report_generation_task(self, dataset_id: int, report_type: str, job_id: str):
    _update_job_status(job_id, "RUNNING", progress=30)
    db: Session = SessionLocal()
    try:
        dataset_data = storage_service.load_dataset(dataset_id, db=db)
        if not dataset_data:
            raise ValueError(f"Dataset #{dataset_id} not found in persistent storage.")

        analysis = dataset_data.get("analysis", {})
        payload = {
            "dataset_id": dataset_id,
            "report_type": report_type,
            "summary": analysis
        }
        _update_job_status(job_id, "SUCCESS", progress=100, result_data=payload)
        return payload
    except Exception as exc:
        _update_job_status(job_id, "FAILED", error_msg=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            pass
        raise exc
    finally:
        db.close()

import socket

def _is_redis_available(host: str = "localhost", port: int = 6379) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=0.1)
        s.close()
        return True
    except Exception:
        return False

def dispatch_job(task_name: str, dataset_id: int, db: Session, task_kwargs: Optional[Dict[str, Any]] = None, org_id: str = "org_default", owner_user_id: Optional[int] = None) -> Dict[str, Any]:
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    task_kwargs = task_kwargs or {}

    db_job = Job(
        job_id=job_id,
        org_id=org_id,
        owner_user_id=owner_user_id,
        dataset_id=dataset_id,
        task_type=task_name,
        status="QUEUED",
        progress=0
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    use_celery = _is_redis_available()
    celery_task_id = None

    if use_celery:
        try:
            if task_name == "PROFILING":
                t_res = profile_dataset_task.delay(dataset_id, job_id)
                celery_task_id = t_res.id
            elif task_name == "ANOMALY_DETECTION":
                t_res = anomaly_detection_task.delay(dataset_id, job_id)
                celery_task_id = t_res.id
            elif task_name == "REMEDIATION":
                t_res = apply_corrections_task.delay(dataset_id, task_kwargs.get("cell_edits", []), task_kwargs.get("strategies", []), job_id)
                celery_task_id = t_res.id
            elif task_name == "REPORT_GENERATION":
                t_res = report_generation_task.delay(dataset_id, task_kwargs.get("report_type", "SUMMARY"), job_id)
                celery_task_id = t_res.id

            if celery_task_id:
                db_job.celery_task_id = celery_task_id
                db.commit()
        except Exception:
            use_celery = False

    if not use_celery:
        # Synchronous execution fallback for environments where Redis is not active
        try:
            if task_name == "PROFILING":
                profile_dataset_task(dataset_id, job_id)
            elif task_name == "ANOMALY_DETECTION":
                anomaly_detection_task(dataset_id, job_id)
            elif task_name == "REMEDIATION":
                apply_corrections_task(dataset_id, task_kwargs.get("cell_edits", []), task_kwargs.get("strategies", []), job_id)
            elif task_name == "REPORT_GENERATION":
                report_generation_task(dataset_id, task_kwargs.get("report_type", "SUMMARY"), job_id)
        except Exception:
            pass

    db.refresh(db_job)
    return {
        "job_id": db_job.job_id,
        "dataset_id": db_job.dataset_id,
        "task_type": db_job.task_type,
        "status": db_job.status,
        "progress": db_job.progress,
        "result_data": db_job.result_data,
        "error_message": db_job.error_message
    }
