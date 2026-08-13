import pandas as pd
from services.agents.dataset_profiling_agent import DatasetProfilingAgent
from services.agents.missing_value_agent import MissingValueAgent
from services.agents.duplicate_detection_agent import DuplicateDetectionAgent
from services.agents.format_validation_agent import FormatValidationAgent
from services.agents.data_quality_score_agent import DataQualityScoreAgent
from services.agents.ai_anomaly_detection_agent import AIAnomalyDetectionAgent
from services.agents.explainability_agent import ExplainabilityAgent
from services.agents.intelligent_auto_correction_agent import IntelligentAutoCorrectionAgent
from services.agents.rule_engine_agent import RuleEngineAgent
from services.agents.monitoring_agent import MonitoringAgent
from services.agents.dataset_chat_agent import DatasetChatAgent
from services.agents.export_agent import ExportAgent

class CoordinatorAgent:
    def __init__(self):
        self.profiling_agent = DatasetProfilingAgent()
        self.missing_agent = MissingValueAgent()
        self.duplicate_agent = DuplicateDetectionAgent()
        self.format_agent = FormatValidationAgent()
        self.quality_agent = DataQualityScoreAgent()
        self.anomaly_agent = AIAnomalyDetectionAgent()
        self.explainability_agent = ExplainabilityAgent()
        self.correction_agent = IntelligentAutoCorrectionAgent()
        self.rule_agent = RuleEngineAgent()
        self.monitoring_agent = MonitoringAgent()
        self.chat_agent = DatasetChatAgent()
        self.export_agent = ExportAgent()

    def process_dataset(self, dataset_id: int, file_path: str) -> dict:
        # Load dataset into Pandas DataFrame
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # 1. Dataset Profiling Agent
        profile_res = self.profiling_agent.execute(df)

        # 2. Missing Value Agent
        missing_res = self.missing_agent.execute(df)

        # 3. Duplicate Detection Agent
        dup_res = self.duplicate_agent.execute(df)

        # 4. Format Validation Agent
        format_res = self.format_agent.execute(df)

        # 5. Quality Score Agent
        quality_res = self.quality_agent.execute(df, missing_res, dup_res, format_res)

        # 6. AI Anomaly Detection Agent (Isolation Forest)
        anomaly_res = self.anomaly_agent.execute(df)

        # 7. Explainability Agent (SHAP)
        explain_res = self.explainability_agent.execute(df, anomaly_res.get("anomalies", []))

        # 8. Intelligent Auto Correction Agent
        correction_res = self.correction_agent.execute(
            df,
            missing_res.get("suggestions", []),
            dup_res.get("suggested_action", "")
        )

        # 9. Monitoring Agent
        monitor_res = self.monitoring_agent.execute(dataset_id, quality_res.get("overall_score", 0.0))

        # 10. Dataset Chat Agent Indexing
        self.chat_agent.index_dataset(dataset_id, df)

        return {
            "dataset_id": dataset_id,
            "status": "COMPLETED",
            "profile": profile_res,
            "missing": missing_res,
            "duplicates": dup_res,
            "formats": format_res,
            "quality_score": quality_res,
            "anomalies": anomaly_res,
            "explainability": explain_res,
            "corrections": correction_res,
            "monitoring": monitor_res
        }
