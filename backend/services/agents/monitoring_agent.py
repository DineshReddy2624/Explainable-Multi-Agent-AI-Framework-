import datetime

class MonitoringAgent:
    def __init__(self):
        self.name = "Monitoring Agent"

    def execute(self, dataset_id: int, quality_score: float) -> dict:
        status = "OPTIMAL" if quality_score >= 85.0 else ("WARNING" if quality_score >= 70.0 else "CRITICAL")
        
        telemetry = [
            {"metric_name": "Overall Quality Score", "metric_value": quality_score, "status": status},
            {"metric_name": "API Service Health", "metric_value": 100.0, "status": "OPTIMAL"},
            {"metric_name": "SQLite Database Latency", "metric_value": 2.4, "status": "OPTIMAL"}
        ]

        return {
            "agent": self.name,
            "dataset_id": dataset_id,
            "status": status,
            "telemetry": telemetry,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
