import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

class AIAnomalyDetectionAgent:
    def __init__(self):
        self.name = "AI Anomaly Detection Agent"

    def execute(self, df: pd.DataFrame) -> dict:
        # Select numeric columns for Isolation Forest
        numeric_df = df.select_dtypes(include=[np.number]).fillna(0)
        
        if numeric_df.empty or len(numeric_df.columns) == 0 or len(numeric_df) < 3:
            return {
                "agent": self.name,
                "anomalies_detected": 0,
                "anomalies": []
            }

        model = IsolationForest(contamination=0.05, random_state=42)
        preds = model.fit_predict(numeric_df)
        scores = model.decision_function(numeric_df)

        anomalies = []
        for idx, (pred, score) in enumerate(zip(preds, scores)):
            if pred == -1: # Anomaly
                anomalies.append({
                    "row_index": idx,
                    "anomaly_score": round(float(-score), 4),
                    "row_data": df.iloc[idx].to_dict()
                })

        return {
            "agent": self.name,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
        }
