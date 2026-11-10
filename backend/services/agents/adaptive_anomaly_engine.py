import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

class AdaptiveAnomalyEngine:
    def __init__(self):
        pass

    def detect_anomalies(self, df: pd.DataFrame) -> dict:
        return self.run_adaptive_analysis(df)

    def run_adaptive_analysis(self, df: pd.DataFrame) -> dict:

        if df is None or df.empty:
            return self._empty_result()

        total_rows = len(df)
        total_cols = len(df.columns)
        headers = list(df.columns)

        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if not any(id_k in c.lower() for id_k in ["id", "key", "index"])]
        categorical_cols = [c for c in df.columns if c not in numeric_cols]

        # 1. Step 1: Analyze Dataset Characteristics
        null_cells = int(df.isnull().sum().sum())
        total_cells = total_rows * total_cols if total_rows * total_cols > 0 else 1
        missing_pct = round((null_cells / total_cells) * 100, 2)
        duplicate_pct = round((df.duplicated().sum() / total_rows) * 100, 2) if total_rows > 0 else 0.0

        # Calculate skewness for numeric columns
        skewness_map = {}
        abs_skews = []
        for col in numeric_cols:
            clean_ser = df[col].dropna()
            if len(clean_ser) >= 3:
                sk = float(clean_ser.skew())
                skewness_map[col] = round(sk, 2)
                abs_skews.append(abs(sk))

        avg_skew = float(np.mean(abs_skews)) if len(abs_skews) > 0 else 0.0
        distribution_type = "Approximately Normal" if avg_skew < 0.6 else "Skewed Distribution"
        has_high_dim = total_cols >= 5
        has_mixed_types = len(numeric_cols) > 0 and len(categorical_cols) > 0

        characteristics = {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "numeric_count": len(numeric_cols),
            "categorical_count": len(categorical_cols),
            "missing_pct": missing_pct,
            "duplicate_pct": duplicate_pct,
            "avg_skewness": round(avg_skew, 2),
            "distribution_type": distribution_type,
            "has_high_dim": has_high_dim,
            "has_mixed_types": has_mixed_types,
            "skewness_map": skewness_map
        }

        # 2. Step 2: Intelligent Rule Engine
        selected_rules = []
        if len(numeric_cols) > 0:
            if avg_skew < 0.6:
                selected_rules.append({
                    "rule": "Rule 1: Normal Distribution Detected",
                    "algorithm": "Z-Score",
                    "reason": f"Numeric features are approximately normally distributed (Average Skewness: {round(avg_skew, 2)})."
                })
            else:
                selected_rules.append({
                    "rule": "Rule 2: Skewed Distribution Detected",
                    "algorithm": "IQR (Interquartile Range)",
                    "reason": f"Numeric features exhibit skewness (Average Skewness: {round(avg_skew, 2)}). IQR is robust against non-normal bounds."
                })

            if has_high_dim:
                selected_rules.append({
                    "rule": "Rule 3 & 6: High Dimensionality Dataset",
                    "algorithm": "Isolation Forest",
                    "reason": f"Dataset contains {total_cols} columns. Isolation Forest efficiently isolates anomalies in high-dimensional feature spaces."
                })

            if total_rows >= 10:
                selected_rules.append({
                    "rule": "Rule 4: Natural Density Clusters",
                    "algorithm": "Local Outlier Factor (LOF)",
                    "reason": "Evaluates local density of data points relative to k-nearest neighbors to identify isolated clusters."
                })

                selected_rules.append({
                    "rule": "Rule 5: Spatial Noise & Cluster Regions",
                    "algorithm": "DBSCAN",
                    "reason": "Identifies spatial cluster outliers and unclustered noise points without assuming spherical clusters."
                })

        # Fallback if no numeric cols
        if not selected_rules:
            selected_rules.append({
                "rule": "Rule 9: General Dataset Rule",
                "algorithm": "IQR (Interquartile Range)",
                "reason": "Standard robust metric for general tabular features."
            })

        # 3. Step 3: Multi-Algorithm Execution
        algo_flags = {rule["algorithm"]: set() for rule in selected_rules}

        # Prepare normalized numeric matrix
        if len(numeric_cols) > 0 and total_rows >= 5:
            num_df = df[numeric_cols].fillna(df[numeric_cols].median())
            scaler = StandardScaler()
            scaled_matrix = scaler.fit_transform(num_df)

            # Execution 1: Z-Score
            if "Z-Score" in algo_flags:
                z_scores = np.abs(stats.zscore(num_df, nan_policy='omit'))
                for r_idx in range(total_rows):
                    if np.any(z_scores[r_idx] > 2.8):
                        algo_flags["Z-Score"].add(r_idx)

            # Execution 2: IQR
            if "IQR (Interquartile Range)" in algo_flags:
                for col in numeric_cols:
                    q1 = num_df[col].quantile(0.25)
                    q3 = num_df[col].quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outlier_mask = (num_df[col] < lower_bound) | (num_df[col] > upper_bound)
                    for r_idx in num_df[outlier_mask].index:
                        algo_flags["IQR (Interquartile Range)"].add(r_idx)

            # Execution 3: Isolation Forest
            if "Isolation Forest" in algo_flags:
                iso = IsolationForest(contamination='auto', random_state=42)
                iso_preds = iso.fit_predict(scaled_matrix)
                for r_idx, pred in enumerate(iso_preds):
                    if pred == -1:
                        algo_flags["Isolation Forest"].add(r_idx)

            # Execution 4: Local Outlier Factor (LOF)
            if "Local Outlier Factor (LOF)" in algo_flags:
                n_neighbors = min(20, max(2, total_rows - 1))
                lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination='auto')
                lof_preds = lof.fit_predict(scaled_matrix)
                for r_idx, pred in enumerate(lof_preds):
                    if pred == -1:
                        algo_flags["Local Outlier Factor (LOF)"].add(r_idx)

            # Execution 5: DBSCAN
            if "DBSCAN" in algo_flags:
                dbscan = DBSCAN(eps=1.5, min_samples=3)
                db_preds = dbscan.fit_predict(scaled_matrix)
                for r_idx, pred in enumerate(db_preds):
                    if pred == -1:
                        algo_flags["DBSCAN"].add(r_idx)

        # 4. Step 4 & 5: Ensemble Decision & Explainability Rationale
        executed_algos = list(algo_flags.keys())
        total_exec_count = len(executed_algos)

        # Gather all flagged row indices
        all_flagged_rows = set()
        for s in algo_flags.values():
            all_flagged_rows.update(s)

        ensemble_results = []
        algo_detection_counts = {algo: len(rows) for algo, rows in algo_flags.items()}

        medians = df[numeric_cols].median().fillna(0) if len(numeric_cols) > 0 else None
        stds = df[numeric_cols].std().replace(0, 1).fillna(1) if len(numeric_cols) > 0 else None

        for r_idx in sorted(all_flagged_rows):
            flagged_by_algos = [algo for algo in executed_algos if r_idx in algo_flags[algo]]
            flag_count = len(flagged_by_algos)

            # Filter: Require at least 2 algorithms consensus OR both Z-Score & IQR statistical outlier agreement
            is_stat_outlier = ("Z-Score" in flagged_by_algos and "IQR (Interquartile Range)" in flagged_by_algos)
            if flag_count < 2 and not is_stat_outlier:
                continue

            # Ensemble confidence percentage
            confidence_pct = round((flag_count / total_exec_count) * 100, 1)

            # Find top contributing numeric feature
            top_feature = numeric_cols[0] if len(numeric_cols) > 0 else (headers[0] if len(headers) > 0 else "Column")
            top_val = df.iloc[r_idx][top_feature] if top_feature in df.columns else 0.0
            med_val = 0.0

            if len(numeric_cols) > 0 and medians is not None and stds is not None:
                row_vals = pd.to_numeric(df.iloc[r_idx][numeric_cols], errors="coerce").fillna(0)
                z_devs = ((row_vals - medians) / stds).abs()
                if not z_devs.empty:
                    top_feature = z_devs.idxmax()
                    top_val = df.iloc[r_idx][top_feature]
                    med_val = round(float(medians[top_feature]), 2)

            explanation = (
                f"Feature '{top_feature}' value ({top_val}) deviates significantly from column median ({med_val}). "
                f"Flagged by {flag_count} of {total_exec_count} adaptive algorithms ({', '.join(flagged_by_algos)})."
            )

            ensemble_results.append({
                "row_index": r_idx,
                "record_id": f"Record #{r_idx + 1}",
                "flagged_algorithms": flagged_by_algos,
                "detection_count": flag_count,
                "total_executed": total_exec_count,
                "final_decision": "Anomaly" if flag_count >= 1 else "Normal",
                "confidence_score": confidence_pct,
                "primary_feature": top_feature,
                "feature_value": float(top_val) if isinstance(top_val, (int, float, np.number)) else str(top_val),
                "explanation": explanation
            })

        # Sort ensemble results by highest confidence score
        ensemble_results = sorted(ensemble_results, key=lambda x: x["confidence_score"], reverse=True)

        return {
            "characteristics": characteristics,
            "selected_rules": selected_rules,
            "executed_algorithms": executed_algos,
            "algo_detection_counts": algo_detection_counts,
            "total_anomalies": len(ensemble_results),
            "ensemble_results": ensemble_results
        }

    def _empty_result(self):
        return {
            "characteristics": {},
            "selected_rules": [],
            "executed_algorithms": [],
            "algo_detection_counts": {},
            "total_anomalies": 0,
            "ensemble_results": []
        }
