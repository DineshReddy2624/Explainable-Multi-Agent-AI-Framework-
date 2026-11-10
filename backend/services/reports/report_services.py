import hashlib
import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


class DatasetProfileService:
    """Provides dynamic dataset profiling, column inventory, and metadata analysis."""

    def analyze_profile(self, before_analysis: Dict[str, Any], after_analysis: Optional[Dict[str, Any]] = None, filename: str = "dataset.csv") -> Dict[str, Any]:
        after_analysis = after_analysis or before_analysis

        total_rows_before = int(before_analysis.get("total_rows", 0))
        total_cols_before = int(before_analysis.get("total_cols", 0))
        total_rows_after = int(after_analysis.get("total_rows", total_rows_before))
        total_cols_after = int(after_analysis.get("total_cols", total_cols_before))

        headers = before_analysis.get("headers", [])
        dt_map = before_analysis.get("datatype_map", {})

        numeric_cols = []
        categorical_cols = []
        datetime_cols = []
        boolean_cols = []
        id_cols = []

        for col in headers:
            col_lower = col.lower()
            dtype = str(dt_map.get(col, "")).lower()

            if any(k in col_lower for k in ["id", "key", "uuid", "code", "index"]):
                id_cols.append(col)
            elif any(k in dtype for k in ["int", "float", "double", "decimal", "number"]):
                numeric_cols.append(col)
            elif any(k in dtype for k in ["date", "time", "timestamp"]):
                datetime_cols.append(col)
            elif any(k in dtype for k in ["bool", "boolean"]):
                boolean_cols.append(col)
            else:
                categorical_cols.append(col)

        # Build column inventory
        missing_map_before = {m["column"]: m["null_count"] for m in before_analysis.get("missing_report", [])}
        inventory = []

        for col in headers:
            dtype = str(dt_map.get(col, "object"))
            miss_cnt = missing_map_before.get(col, 0)
            miss_pct = round((miss_cnt / max(1, total_rows_before)) * 100, 2)
            non_null = total_rows_before - miss_cnt
            
            # Status
            if miss_cnt == 0:
                status = "PASSED ✓"
            elif miss_pct < 10.0:
                status = "MINOR MISSING ⚠️"
            else:
                status = "CRITICAL MISSING ❌"

            inventory.append({
                "column": col,
                "data_type": dtype,
                "non_null_count": non_null,
                "missing_count": miss_cnt,
                "missing_pct": miss_pct,
                "status": status
            })

        # Extract numeric column statistical profiles
        stats_b = before_analysis.get("stats_summary", {})
        stats_a = after_analysis.get("stats_summary", {})
        numeric_stats = []

        for col in numeric_cols:
            sb = stats_b.get(col, {})
            sa = stats_a.get(col, {})
            numeric_stats.append({
                "column": col,
                "mean_before": sb.get("mean", "N/A"),
                "mean_after": sa.get("mean", "N/A"),
                "median_before": sb.get("median", "N/A"),
                "median_after": sa.get("median", "N/A"),
                "std_before": sb.get("std", "N/A"),
                "std_after": sa.get("std", "N/A"),
                "min_before": sb.get("min", "N/A"),
                "min_after": sa.get("min", "N/A"),
                "max_before": sb.get("max", "N/A"),
                "max_after": sa.get("max", "N/A")
            })

        return {
            "filename": filename,
            "total_rows_before": total_rows_before,
            "total_cols_before": total_cols_before,
            "total_rows_after": total_rows_after,
            "total_cols_after": total_cols_after,
            "row_delta": total_rows_after - total_rows_before,
            "col_delta": total_cols_after - total_cols_before,
            "numeric_cols": numeric_cols,
            "categorical_cols": categorical_cols,
            "datetime_cols": datetime_cols,
            "boolean_cols": boolean_cols,
            "id_cols": id_cols,
            "column_inventory": inventory,
            "numeric_stats": numeric_stats
        }



class QualityAssessmentService:
    """Calculates multidimensional quality scores and severity ratings dynamically."""

    def evaluate_quality(self, before_analysis: Dict[str, Any], after_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        after_analysis = after_analysis or before_analysis

        b_scores = before_analysis.get("quality_scores", {})
        a_scores = after_analysis.get("quality_scores", {})

        b_overall = float(b_scores.get("overall_score", 0.0))
        a_overall = float(a_scores.get("overall_score", b_overall))
        improvement = round(max(0.0, a_overall - b_overall), 2)

        def get_severity(score: float) -> Tuple[str, str]:
            if score >= 90.0:
                return "EXCELLENT", "LOW RISK"
            elif score >= 75.0:
                return "GOOD", "MODERATE RISK"
            elif score >= 50.0:
                return "NEEDS IMPROVEMENT", "HIGH RISK"
            else:
                return "CRITICAL", "SEVERE RISK"

        b_rating, b_risk = get_severity(b_overall)
        a_rating, a_risk = get_severity(a_overall)

        dimensions = [
            {
                "name": "Completeness",
                "weight": "30%",
                "before": float(b_scores.get("completeness", 100.0)),
                "after": float(a_scores.get("completeness", 100.0)),
                "explanation": "Evaluates proportion of non-null, populated data cells across all attributes."
            },
            {
                "name": "Uniqueness",
                "weight": "25%",
                "before": float(b_scores.get("uniqueness", 100.0)),
                "after": float(a_scores.get("uniqueness", 100.0)),
                "explanation": "Evaluates absence of duplicate rows and redundant record keys."
            },
            {
                "name": "Validity",
                "weight": "25%",
                "before": float(b_scores.get("validity", 100.0)),
                "after": float(a_scores.get("validity", 100.0)),
                "explanation": "Evaluates adherence to format rules (regex, ranges, types, dates)."
            },
            {
                "name": "Consistency",
                "weight": "10%",
                "before": float(b_scores.get("consistency", 100.0)),
                "after": float(a_scores.get("consistency", 100.0)),
                "explanation": "Evaluates absence of statistical outliers, ML anomalies, and spatial noise."
            },
            {
                "name": "Accuracy",
                "weight": "10%",
                "before": float(b_scores.get("accuracy", 95.0)),
                "after": float(a_scores.get("accuracy", 95.0)),
                "explanation": "Evaluates domain constraint integrity and value bounds reliability."
            }
        ]

        for d in dimensions:
            d["delta"] = round(d["after"] - d["before"], 2)
            d["status"] = "IMPROVED ✓" if d["delta"] > 0 else ("OPTIMAL ✓" if d["after"] >= 99.0 else "UNCHANGED")

        return {
            "before_overall": b_overall,
            "after_overall": a_overall,
            "improvement": improvement,
            "before_rating": b_rating,
            "after_rating": a_rating,
            "before_risk": b_risk,
            "after_risk": a_risk,
            "dimensions": dimensions
        }


class MissingValueAnalysisService:
    """Analyzes column-level missing values and evaluates imputation performance."""

    def analyze_missing(self, before_analysis: Dict[str, Any], after_analysis: Optional[Dict[str, Any]] = None, logs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        logs = logs or []
        after_analysis = after_analysis or before_analysis

        m_before = before_analysis.get("missing_report", [])
        m_after_map = {m["column"]: m["null_count"] for m in after_analysis.get("missing_report", [])}
        dt_map = before_analysis.get("datatype_map", {})
        total_rows = before_analysis.get("total_rows", 1)

        # Build column strategy lookup from remediation logs
        strategy_map = {}
        for log in logs:
            col = log.get("column_name")
            ctype = log.get("correction_type", "")
            if col and ("Imputation" in ctype or "Fill" in ctype):
                strategy_map[col] = ctype

        details = []
        total_missing_before = 0
        total_missing_after = 0

        for item in m_before:
            col = item["column"]
            cnt_before = item["null_count"]
            pct_before = item["missing_pct"]
            cnt_after = m_after_map.get(col, 0)
            
            total_missing_before += cnt_before
            total_missing_after += cnt_after

            dtype = str(dt_map.get(col, "numeric"))
            is_num = any(k in dtype.lower() for k in ["int", "float", "double", "decimal"])

            rec_strategy = "Median Imputation" if is_num else "Mode / Categorical Imputation"
            actual_strategy = strategy_map.get(col, rec_strategy if len(logs) > 0 else "None")

            details.append({
                "column": col,
                "missing_before": cnt_before,
                "missing_pct": pct_before,
                "data_type": dtype,
                "recommended_strategy": rec_strategy,
                "actual_strategy": actual_strategy,
                "missing_after": cnt_after,
                "resolved_count": cnt_before - cnt_after,
                "status": "RESOLVED ✓" if cnt_after == 0 else "PARTIAL ⚠️"
            })

        has_missing = len(details) > 0

        return {
            "has_missing": has_missing,
            "total_missing_before": total_missing_before,
            "total_missing_after": total_missing_after,
            "total_resolved": total_missing_before - total_missing_after,
            "details": details
        }


class DuplicateAnalysisService:
    """Analyzes duplicate rows and deduplication effectiveness."""

    def analyze_duplicates(self, before_analysis: Dict[str, Any], after_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        after_analysis = after_analysis or before_analysis

        dup_before = int(before_analysis.get("duplicate_count", 0))
        dup_after = int(after_analysis.get("duplicate_count", 0))
        rows_before = int(before_analysis.get("total_rows", 0))
        rows_after = int(after_analysis.get("total_rows", rows_before))

        dup_pct_before = round((dup_before / max(1, rows_before)) * 100, 2)
        dup_pct_after = round((dup_after / max(1, rows_after)) * 100, 2)

        removed_count = max(0, dup_before - dup_after)
        has_duplicates = dup_before > 0

        return {
            "has_duplicates": has_duplicates,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "duplicates_before": dup_before,
            "dup_pct_before": dup_pct_before,
            "duplicates_after": dup_after,
            "dup_pct_after": dup_pct_after,
            "duplicates_removed": removed_count,
            "rows_retained": rows_after,
            "status": "CLEANED ✓" if dup_after == 0 and has_duplicates else ("OPTIMAL ✓" if not has_duplicates else "RESIDUAL DUP ⚠️")
        }


class FormatValidationService:
    """Analyzes format compliance (email, phone, age, currency, dates)."""

    def analyze_formats(self, before_analysis: Dict[str, Any], after_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        after_analysis = after_analysis or before_analysis

        fmt_before = before_analysis.get("format_issues", [])
        fmt_after = after_analysis.get("format_issues", [])

        total_rows = int(before_analysis.get("total_rows", 1))

        # Group by column and format type
        col_summary = {}
        for item in fmt_before:
            col = item["column"]
            fmt_type = item.get("expected_format", "Format Error")
            if col not in col_summary:
                col_summary[col] = {
                    "column": col,
                    "expected_pattern": fmt_type,
                    "invalid_before": 0,
                    "examples": set()
                }
            col_summary[col]["invalid_before"] += 1
            if len(col_summary[col]["examples"]) < 3 and item.get("invalid_value"):
                col_summary[col]["examples"].add(str(item["invalid_value"]))

        # Build after map
        after_counts = {}
        for item in fmt_after:
            col = item["column"]
            after_counts[col] = after_counts.get(col, 0) + 1

        details = []
        total_invalid_before = len(fmt_before)
        total_invalid_after = len(fmt_after)

        for col, data in col_summary.items():
            inv_before = data["invalid_before"]
            inv_after = after_counts.get(col, 0)
            pct_before = round((inv_before / max(1, total_rows)) * 100, 2)
            
            remediation = "Regex Standardized & Cleaned" if inv_after < inv_before else "Reviewed"
            example_str = ", ".join(list(data["examples"])[:2])

            details.append({
                "column": col,
                "expected_pattern": data["expected_pattern"],
                "invalid_before": inv_before,
                "invalid_pct_before": pct_before,
                "sample_invalid": example_str if example_str else "N/A",
                "remediation_applied": remediation,
                "invalid_after": inv_after,
                "status": "STANDARDIZED ✓" if inv_after == 0 else "PARTIAL ⚠️"
            })

        has_format_issues = total_invalid_before > 0

        return {
            "has_format_issues": has_format_issues,
            "total_invalid_before": total_invalid_before,
            "total_invalid_after": total_invalid_after,
            "total_corrected": total_invalid_before - total_invalid_after,
            "details": details
        }


class AnomalyAnalysisService:
    """Analyzes ML anomaly detection ensemble findings and remediation bounds."""

    def analyze_anomalies(self, before_analysis: Dict[str, Any], after_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        after_analysis = after_analysis or before_analysis

        anom_before = before_analysis.get("anomalies", [])
        anom_after = after_analysis.get("anomalies", [])

        adaptive_before = before_analysis.get("adaptive_analysis", {})
        selected_rules = adaptive_before.get("selected_rules", [])
        exec_algos = adaptive_before.get("executed_algorithms", ["Isolation Forest", "LOF", "DBSCAN", "Z-Score", "IQR"])

        total_before = len(anom_before)
        total_after = len(anom_after)
        total_rows = int(before_analysis.get("total_rows", 1))

        pct_before = round((total_before / max(1, total_rows)) * 100, 2)
        pct_after = round((total_after / max(1, total_rows)) * 100, 2)

        # Count affected columns
        col_counts = {}
        for a in anom_before:
            col = a.get("column", "Numeric Column")
            col_counts[col] = col_counts.get(col, 0) + 1

        algos_str = ", ".join(exec_algos) if exec_algos else "Adaptive ML Ensemble (Isolation Forest, LOF, Z-Score, IQR)"

        has_anomalies = total_before > 0

        return {
            "has_anomalies": has_anomalies,
            "algorithms": algos_str,
            "executed_algorithms": exec_algos,
            "selected_rules": selected_rules,
            "anomalies_before": total_before,
            "pct_before": pct_before,
            "anomalies_after": total_after,
            "pct_after": pct_after,
            "anomalies_remediated": max(0, total_before - total_after),
            "affected_columns": col_counts,
            "status": "REMEDIATED ✓" if total_after <= 1 and has_anomalies else ("OPTIMAL ✓" if not has_anomalies else "RESIDUAL ANOMALIES ⚠️")
        }


class RemediationSummaryService:
    """Aggregates all remediation actions and correction log entries."""

    def summarize_remediation(self, logs: List[Dict[str, Any]], before_analysis: Dict[str, Any], after_analysis: Dict[str, Any]) -> Dict[str, Any]:
        category_counts = {}
        for log in logs:
            ctype = log.get("correction_type", "Data Correction")
            category_counts[ctype] = category_counts.get(ctype, 0) + 1

        # Map to high-level categories
        missing_count = sum(cnt for ctype, cnt in category_counts.items() if "Imputation" in ctype or "Fill" in ctype)
        format_count = sum(cnt for ctype, cnt in category_counts.items() if "Format" in ctype or "Regex" in ctype or "Phone" in ctype or "Email" in ctype)
        outlier_count = sum(cnt for ctype, cnt in category_counts.items() if "Outlier" in ctype or "Bounding" in ctype or "IQR" in ctype)
        duplicate_ops = sum(cnt for ctype, cnt in category_counts.items() if "Duplicate" in ctype or "Deduplication" in ctype)

        total_ops = len(logs)

        categories = [
            {
                "category": "Missing Value Imputation",
                "corrections_applied": missing_count,
                "method": "Median / Mode Imputation",
                "status": "Applied ✓" if missing_count > 0 else "None Required"
            },
            {
                "category": "Format & Regex Standardization",
                "corrections_applied": format_count,
                "method": "Regex Normalization & String Repair",
                "status": "Applied ✓" if format_count > 0 else "None Required"
            },
            {
                "category": "ML Outlier & Range Bounding",
                "corrections_applied": outlier_count,
                "method": "IQR & Percentile Clipping",
                "status": "Applied ✓" if outlier_count > 0 else "None Required"
            },
            {
                "category": "Duplicate Rows Deduplication",
                "corrections_applied": duplicate_ops,
                "method": "Exact Row Deduplication",
                "status": "Applied ✓" if duplicate_ops > 0 else "None Required"
            }
        ]

        return {
            "total_operations": total_ops,
            "category_counts": category_counts,
            "categories": categories
        }


class BeforeAfterComparisonService:
    """Generates master comparison matrix and column-level comparison grid."""

    def build_comparison(self, before_analysis: Dict[str, Any], after_analysis: Dict[str, Any]) -> Dict[str, Any]:
        rows_b = int(before_analysis.get("total_rows", 0))
        rows_a = int(after_analysis.get("total_rows", rows_b))
        cols_b = int(before_analysis.get("total_cols", 0))
        cols_a = int(after_analysis.get("total_cols", cols_b))

        miss_b = int(before_analysis.get("total_missing_cells", 0))
        miss_a = int(after_analysis.get("total_missing_cells", 0))

        dup_b = int(before_analysis.get("duplicate_count", 0))
        dup_a = int(after_analysis.get("duplicate_count", 0))

        fmt_b = len(before_analysis.get("format_issues", []))
        fmt_a = len(after_analysis.get("format_issues", []))

        anom_b = len(before_analysis.get("anomalies", []))
        anom_a = len(after_analysis.get("anomalies", []))

        b_score = float(before_analysis.get("quality_scores", {}).get("overall_score", 0.0))
        a_score = float(after_analysis.get("quality_scores", {}).get("overall_score", b_score))

        master_rows = [
            {"metric": "Row Count", "before": str(rows_b), "after": str(rows_a), "change": str(rows_a - rows_b), "status": "Deduplicated" if rows_a < rows_b else "Preserved"},
            {"metric": "Column Count", "before": str(cols_b), "after": str(cols_a), "change": "0", "status": "Preserved"},
            {"metric": "Missing Data Cells", "before": str(miss_b), "after": str(miss_a), "change": str(miss_a - miss_b), "status": "Resolved" if miss_a == 0 else "Partial"},
            {"metric": "Duplicate Rows", "before": str(dup_b), "after": str(dup_a), "change": str(dup_a - dup_b), "status": "Resolved" if dup_a == 0 else "Partial"},
            {"metric": "Format Errors", "before": str(fmt_b), "after": str(fmt_a), "change": str(fmt_a - fmt_b), "status": "Resolved" if fmt_a == 0 else "Partial"},
            {"metric": "ML Ensemble Anomalies", "before": str(anom_b), "after": str(anom_a), "change": str(anom_a - anom_b), "status": "Remediated" if anom_a < anom_b else "Evaluated"},
            {"metric": "Overall Quality Score", "before": f"{b_score:.1f}%", "after": f"{a_score:.1f}%", "change": f"+{max(0.0, a_score - b_score):.1f}%", "status": "OPTIMAL ✓" if a_score >= 95.0 else "IMPROVED"}
        ]

        # Column-level comparison
        headers = before_analysis.get("headers", [])
        m_b_map = {m["column"]: m["null_count"] for m in before_analysis.get("missing_report", [])}
        m_a_map = {m["column"]: m["null_count"] for m in after_analysis.get("missing_report", [])}

        f_b_map = {}
        for f in before_analysis.get("format_issues", []):
            f_b_map[f["column"]] = f_b_map.get(f["column"], 0) + 1

        f_a_map = {}
        for f in after_analysis.get("format_issues", []):
            f_a_map[f["column"]] = f_a_map.get(f["column"], 0) + 1

        col_grid = []
        for col in headers:
            mb = m_b_map.get(col, 0)
            ma = m_a_map.get(col, 0)
            fb = f_b_map.get(col, 0)
            fa = f_a_map.get(col, 0)

            col_grid.append({
                "column": col,
                "missing_before": mb,
                "missing_after": ma,
                "format_before": fb,
                "format_after": fa,
                "status": "PASSED ✓" if ma == 0 and fa == 0 else "ATTENTION ⚠️"
            })

        return {
            "master_rows": master_rows,
            "column_grid": col_grid
        }


class AuditTrailService:
    """Formats audit trail logs and calculates cryptographic audit hash."""

    def format_audit(self, logs: List[Dict[str, Any]], dataset_id: int = 1, org_id: str = "org_default") -> Dict[str, Any]:
        total_records = len(logs)

        # Compute SHA-256 digital audit hash
        hasher = hashlib.sha256()
        for log in logs:
            hasher.update(str(log).encode("utf-8"))
        digital_hash = f"0x{hasher.hexdigest()[:16].upper()}"

        # Sample logs for large datasets
        first_n = logs[:5]
        last_n = logs[-5:] if total_records > 5 else []

        return {
            "total_audit_records": total_records,
            "digital_hash": digital_hash,
            "first_n": first_n,
            "last_n": last_n,
            "audit_available": True
        }


class ReportValidationService:
    """
    Data Reconciliation Validation Engine.
    Ensures report metrics reconcile mathematically before PDF rendering.
    """

    def validate_reconciliation(self, before_analysis: Dict[str, Any], after_analysis: Dict[str, Any], logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        discrepancies = []

        rows_b = int(before_analysis.get("total_rows", 0))
        rows_a = int(after_analysis.get("total_rows", rows_b))

        dup_b = int(before_analysis.get("duplicate_count", 0))
        dup_a = int(after_analysis.get("duplicate_count", 0))

        # Check 1: Row count change must align with duplicate row removal or explicit drop actions
        expected_rows_a = rows_b - (dup_b - dup_a)
        if len(logs) > 0 and dup_b > 0 and rows_a > expected_rows_a:
            discrepancies.append(
                f"Row count discrepancy: Raw rows ({rows_b}) minus removed duplicates ({dup_b - dup_a}) "
                f"equals {expected_rows_a}, but cleaned dataset has {rows_a} rows."
            )

        # Check 2: Missing cell resolution sanity
        miss_b = int(before_analysis.get("total_missing_cells", 0))
        miss_a = int(after_analysis.get("total_missing_cells", 0))
        if miss_a > miss_b:
            discrepancies.append(
                f"Missing cell discrepancy: Cleaned dataset missing cells ({miss_a}) exceeded raw dataset missing cells ({miss_b})."
            )

        # Check 3: Percentage validation bounds
        b_score = float(before_analysis.get("quality_scores", {}).get("overall_score", 0.0))
        a_score = float(after_analysis.get("quality_scores", {}).get("overall_score", b_score))
        if not (0.0 <= b_score <= 100.0) or not (0.0 <= a_score <= 100.0):
            discrepancies.append(
                f"Quality score out-of-bounds: Before score {b_score}% or After score {a_score}% invalid."
            )

        is_valid = len(discrepancies) == 0

        return {
            "is_valid": is_valid,
            "discrepancies": discrepancies,
            "status": "PASSED RECONCILIATION ✓" if is_valid else "DATA RECONCILIATION DISCREPANCY DETECTED ❌"
        }
