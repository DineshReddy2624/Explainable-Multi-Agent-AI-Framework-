import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from services.data_engine import data_engine
from services.retrieval.hybrid_retriever import hybrid_retriever

logger = logging.getLogger(__name__)


class BaseTool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement execute()")


class StructuredAnalyticsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="StructuredAnalyticsTool",
            description="Performs deterministic statistical aggregations (mean, median, sum, min, max, std, variance, range, count) on tabular datasets using Pandas."
        )

    def execute(self, df: pd.DataFrame, operation: str, target_column: str, group_by_column: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if df is None or df.empty or target_column not in df.columns:
            return {"success": False, "error": f"Column '{target_column}' not found in dataset."}

        op = operation.upper()
        if group_by_column and group_by_column in df.columns:
            grp_df = df.groupby(group_by_column)[target_column].agg(['count', 'mean', 'median', 'sum']).round(2).reset_index()
            return {
                "success": True,
                "operation": op,
                "target_column": target_column,
                "group_by_column": group_by_column,
                "result_type": "table",
                "data": grp_df.to_dict(orient="records")
            }

        ser = pd.to_numeric(df[target_column], errors='coerce').dropna()
        if ser.empty:
            return {"success": False, "error": f"No valid numerical data in column '{target_column}'."}

        val = 0.0
        if op in ["MEAN", "AVERAGE"]:
            val = round(float(ser.mean()), 2)
        elif op == "MEDIAN":
            val = round(float(ser.median()), 2)
        elif op == "SUM":
            val = round(float(ser.sum()), 2)
        elif op == "MIN":
            val = round(float(ser.min()), 2)
        elif op == "MAX":
            val = round(float(ser.max()), 2)
        elif op in ["STD", "STANDARD_DEVIATION"]:
            val = round(float(ser.std()), 2)
        elif op == "VARIANCE":
            val = round(float(ser.var()), 2)
        elif op == "COUNT":
            val = int(len(ser))
        else:
            val = round(float(ser.mean()), 2)

        return {
            "success": True,
            "operation": op,
            "target_column": target_column,
            "value": val,
            "formatted": f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
        }


class SafeMathTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="SafeMathTool",
            description="Evaluates mathematical expressions safely using AST without dangerous eval() or exec()."
        )

    def execute(self, expression: str, variables: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        from services.agents.dataset_chat_agent import SafeMathEvaluator
        try:
            evaluator = SafeMathEvaluator(variables or {})
            res = evaluator.evaluate(expression)
            if isinstance(res, float):
                res = round(res, 4)
                if res.is_integer():
                    res = int(res)
            return {
                "success": True,
                "expression": expression,
                "value": res,
                "formatted": f"{res:,.4f}".rstrip('0').rstrip('.') if isinstance(res, float) else f"{res:,}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class DataQualityTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="DataQualityTool",
            description="Analyzes missing values, duplicate records, outliers, and data quality scores."
        )

    def execute(self, df: pd.DataFrame, analysis: Dict[str, Any], query_type: str = "missing", **kwargs) -> Dict[str, Any]:
        if df is None or df.empty:
            return {"success": False, "error": "No dataset loaded."}

        total_rows = len(df)
        total_cols = len(df.columns)

        if query_type.lower() in ["missing", "nulls"]:
            null_counts = df.isnull().sum()
            tot_null = int(null_counts.sum())
            missing_report = [{"column": col, "null_count": int(cnt), "missing_pct": round((cnt / total_rows) * 100, 1)} for col, cnt in null_counts[null_counts > 0].items()]
            return {
                "success": True,
                "query_type": "missing_values",
                "total_missing_cells": tot_null,
                "missing_report": missing_report
            }
        elif query_type.lower() in ["duplicates", "duplicate"]:
            dup_cnt = int(df.duplicated().sum())
            return {
                "success": True,
                "query_type": "duplicates",
                "duplicate_count": dup_cnt,
                "total_rows": total_rows
            }
        elif query_type.lower() in ["outliers", "anomalies"]:
            numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
            anom_list = []
            for col in numeric_cols:
                ser = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(ser) > 5:
                    mean_v = ser.mean()
                    std_v = ser.std()
                    if std_v > 0:
                        z_scores = (ser - mean_v) / std_v
                        for idx in z_scores[z_scores.abs() > 3].index:
                            anom_list.append({"row": int(idx) + 1, "column": col, "value": float(df.loc[idx, col]), "z_score": float(round(z_scores[idx], 2))})
            return {
                "success": True,
                "query_type": "outliers",
                "outlier_count": len(anom_list),
                "outliers": anom_list[:50]
            }

        return {"success": True, "query_type": "summary", "total_rows": total_rows, "total_cols": total_cols}


class DocumentSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="DocumentSearchTool",
            description="Performs Hybrid BM25 + Vector Retrieval on uploaded unstructured documents (PDF, DOCX, TXT, MD, HTML, JSON)."
        )

    def execute(self, org_id: str, document_id: Optional[int], query: str, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        results = hybrid_retriever.retrieve(org_id=org_id, document_id=document_id, query=query, top_k=top_k)
        return {
            "success": True,
            "query": query,
            "result_count": len(results),
            "chunks": results
        }


class ChartGenerationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ChartGenerationTool",
            description="Generates interactive chart specification payloads (bar, line, scatter, pie) from dataset queries."
        )

    def execute(self, df: pd.DataFrame, chart_type: str, x_column: str, y_column: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if df is None or df.empty or x_column not in df.columns:
            return {"success": False, "error": f"Invalid x_column '{x_column}' for chart generation."}

        chart_type_clean = chart_type.lower()
        chart_data = []

        if y_column and y_column in df.columns:
            grp = df.groupby(x_column)[y_column].mean().round(2).reset_index().head(20)
            chart_data = grp.to_dict(orient="records")
        else:
            vc = df[x_column].value_counts().head(15).reset_index()
            vc.columns = [x_column, "count"]
            chart_data = vc.to_dict(orient="records")

        return {
            "success": True,
            "chart_type": chart_type_clean,
            "title": f"{chart_type.capitalize()} Chart: {x_column}" + (f" vs {y_column}" if y_column else ""),
            "x_column": x_column,
            "y_column": y_column or "count",
            "data": chart_data
        }


class TimeSeriesTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="TimeSeriesTool",
            description="Analyzes date columns, time series trends, rolling averages, and period metrics."
        )

    def execute(self, df: pd.DataFrame, date_column: str, metric_column: str, freq: str = "M", **kwargs) -> Dict[str, Any]:
        if df is None or df.empty or date_column not in df.columns or metric_column not in df.columns:
            return {"success": False, "error": "Invalid date or metric column for time series analysis."}

        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_column])

        if df_copy.empty:
            return {"success": False, "error": f"No valid date values found in column '{date_column}'."}

        df_copy.set_index(date_column, inplace=True)
        resampled = df_copy[metric_column].resample(freq).mean().round(2).reset_index()
        resampled[date_column] = resampled[date_column].dt.strftime('%Y-%m-%d')

        return {
            "success": True,
            "date_column": date_column,
            "metric_column": metric_column,
            "frequency": freq,
            "trend_data": resampled.to_dict(orient="records")
        }
