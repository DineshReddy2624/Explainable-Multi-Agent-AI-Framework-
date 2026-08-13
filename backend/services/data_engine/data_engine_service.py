import os
import re
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union

BLOCKED_SQL_KEYWORDS = {
    "drop", "delete", "update", "insert", "alter", "create", "attach",
    "detach", "pragma", "copy", "read_csv", "read_parquet", "load",
    "install", "import", "system", "exec", "call", "vacuum", "checkpoint"
}

class DataEngineService:
    def __init__(self):
        pass

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Create a fresh thread-safe in-memory DuckDB connection."""
        return duckdb.connect(database=":memory:")

    def register_dataset(self, con: duckdb.DuckDBPyConnection, target: Union[str, pd.DataFrame]) -> str:
        """
        Register a Parquet filepath or pandas DataFrame as 'dataset_table' view in DuckDB.
        Returns the registered view name.
        """
        if isinstance(target, str) and os.path.exists(target):
            # Escape single quotes in file path
            escaped_path = target.replace("'", "''")
            con.execute(f"CREATE VIEW dataset_table AS SELECT * FROM read_parquet('{escaped_path}')")
        elif isinstance(target, pd.DataFrame):
            con.register("dataset_table", target)
        else:
            raise ValueError(f"Invalid dataset target: {target}")
        return "dataset_table"

    def get_schema(self, target: Union[str, pd.DataFrame]) -> Dict[str, Any]:
        """Fetch schema metadata using PyArrow or DuckDB without loading full dataset into memory."""
        if isinstance(target, str) and os.path.exists(target) and target.endswith(".parquet"):
            pf = pq.ParquetFile(target)
            arrow_schema = pf.schema_arrow
            num_rows = pf.metadata.num_rows
            num_cols = pf.metadata.num_columns
            columns = list(arrow_schema.names)
            types = {arrow_schema.field(i).name: str(arrow_schema.field(i).type) for i in range(num_cols)}
            return {
                "total_rows": num_rows,
                "total_cols": num_cols,
                "columns": columns,
                "types": types
            }
        else:
            with self.get_connection() as con:
                self.register_dataset(con, target)
                res = con.execute("DESCRIBE dataset_table").fetchall()
                count = con.execute("SELECT COUNT(*) FROM dataset_table").fetchone()[0]
                columns = [r[0] for r in res]
                types = {r[0]: r[1] for r in res}
                return {
                    "total_rows": count,
                    "total_cols": len(columns),
                    "columns": columns,
                    "types": types
                }

    def validate_sql_query(self, sql_query: str, allowed_columns: List[str]) -> bool:
        """Validate that SQL query is strictly analytical and read-only."""
        cleaned = sql_query.strip().lower()
        
        # Check for blocked DML/DDL keywords
        words = set(re.findall(r'\b[a-z_]+\b', cleaned))
        if any(bw in words for bw in BLOCKED_SQL_KEYWORDS):
            raise ValueError("SQL query contains unauthorized DML/DDL mutation keywords.")

        if not cleaned.startswith("select") and not cleaned.startswith("with"):
            raise ValueError("Only analytical SELECT queries are permitted.")

        return True

    def execute_safe_query(self, target: Union[str, pd.DataFrame], sql_query: str) -> pd.DataFrame:
        """Execute a validated read-only SQL query against the target dataset."""
        with self.get_connection() as con:
            self.register_dataset(con, target)
            
            # Fetch valid schema columns
            cols = [r[0] for r in con.execute("DESCRIBE dataset_table").fetchall()]
            self.validate_sql_query(sql_query, cols)

            df_res = con.execute(sql_query).df()
            return df_res

    def profile_dataset_duckdb(self, target: Union[str, pd.DataFrame], filename: str = "dataset.csv") -> Dict[str, Any]:
        """Perform out-of-core data profiling using DuckDB aggregation queries."""
        with self.get_connection() as con:
            self.register_dataset(con, target)

            # 1. Total Rows & Columns
            row_count = con.execute("SELECT COUNT(*) FROM dataset_table").fetchone()[0]
            col_info = con.execute("DESCRIBE dataset_table").fetchall()
            headers = [c[0] for c in col_info]
            datatype_map = {c[0]: c[1] for c in col_info}

            # Identify numeric columns
            numeric_cols = []
            for col, dtype in datatype_map.items():
                dtype_upper = dtype.upper()
                if any(t in dtype_upper for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT", "BIGINT"]):
                    numeric_cols.append(col)

            # 2. Numerical Column Statistics
            stats_summary = {}
            if numeric_cols:
                select_exprs = []
                for c in numeric_cols:
                    safe_c = f'"{c}"'
                    select_exprs.extend([
                        f'AVG({safe_c}) AS avg_{c}',
                        f'MEDIAN({safe_c}) AS med_{c}',
                        f'STDDEV({safe_c}) AS std_{c}',
                        f'MIN({safe_c}) AS min_{c}',
                        f'MAX({safe_c}) AS max_{c}'
                    ])
                
                stat_sql = f"SELECT {', '.join(select_exprs)} FROM dataset_table"
                stat_row = con.execute(stat_sql).fetchone()
                
                idx = 0
                for c in numeric_cols:
                    mean_val, med_val, std_val, min_val, max_val = stat_row[idx:idx+5]
                    idx += 5
                    if mean_val is not None:
                        stats_summary[c] = {
                            "mean": round(float(mean_val), 2),
                            "median": round(float(med_val), 2) if med_val is not None else 0.0,
                            "std": round(float(std_val), 2) if std_val is not None else 0.0,
                            "min": round(float(min_val), 2),
                            "max": round(float(max_val), 2)
                        }

            # 3. Missing Value Analysis
            missing_report = []
            total_missing_cells = 0
            
            null_exprs = []
            for c in headers:
                safe_c = f'"{c}"'
                null_exprs.append(
                    f"SUM(CASE WHEN {safe_c} IS NULL OR TRIM(CAST({safe_c} AS VARCHAR)) = '' OR LOWER(TRIM(CAST({safe_c} AS VARCHAR))) = 'nan' THEN 1 ELSE 0 END) AS null_cnt_{c}"
                )

            null_sql = f"SELECT {', '.join(null_exprs)} FROM dataset_table"
            null_counts_row = con.execute(null_sql).fetchone()

            for i, c in enumerate(headers):
                null_cnt = int(null_counts_row[i] or 0)
                total_missing_cells += null_cnt

                if null_cnt > 0:
                    missing_pct = round((null_cnt / row_count) * 100, 2) if row_count > 0 else 0.0
                    mean_val = stats_summary.get(c, {}).get("mean", None)
                    med_val = stats_summary.get(c, {}).get("median", None)

                    missing_report.append({
                        "column": c,
                        "null_count": null_cnt,
                        "missing_pct": missing_pct,
                        "suggested_mean": mean_val,
                        "suggested_median": med_val,
                        "suggested_mode": "N/A"
                    })

            # 4. Duplicate Rows Count
            dup_sql = f"SELECT COUNT(*) - COUNT(DISTINCT *) FROM dataset_table"
            try:
                duplicate_count = int(con.execute(dup_sql).fetchone()[0])
            except Exception:
                duplicate_count = 0

            # 5. Quality Score Calculation
            total_cells = row_count * len(headers) if row_count > 0 else 1
            missing_score = max(0, 100 - (total_missing_cells / total_cells * 100))
            duplicate_score = max(0, 100 - (duplicate_count / max(1, row_count) * 100))
            overall_score = round((missing_score * 0.5) + (duplicate_score * 0.5), 1)

            return {
                "filename": filename,
                "total_rows": row_count,
                "total_cols": len(headers),
                "headers": headers,
                "datatype_map": datatype_map,
                "numeric_cols": numeric_cols,
                "stats_summary": stats_summary,
                "total_missing_cells": total_missing_cells,
                "missing_report": missing_report,
                "duplicate_count": duplicate_count,
                "quality_scores": {
                    "overall_score": overall_score,
                    "missing_score": round(missing_score, 1),
                    "duplicate_score": round(duplicate_score, 1)
                }
            }

    def answer_numerical_query(self, target: Union[str, pd.DataFrame], question: str) -> Optional[Dict[str, Any]]:
        """Answers numerical dataset questions deterministically via DuckDB aggregation queries."""
        q_lower = question.lower()
        
        with self.get_connection() as con:
            self.register_dataset(con, target)
            cols_res = con.execute("DESCRIBE dataset_table").fetchall()
            cols = [c[0] for c in cols_res]

            if any(k in q_lower for k in ["total rows", "row count", "how many rows", "total records"]):
                cnt = con.execute("SELECT COUNT(*) FROM dataset_table").fetchone()[0]
                return {
                    "answer_text": f"The dataset contains exactly {cnt:,} total rows.",
                    "sql_used": "SELECT COUNT(*) FROM dataset_table",
                    "metric_value": cnt
                }

            if any(k in q_lower for k in ["total columns", "column count", "how many columns"]):
                return {
                    "answer_text": f"The dataset contains {len(cols)} columns: {', '.join(cols)}.",
                    "sql_used": "DESCRIBE dataset_table",
                    "metric_value": len(cols)
                }

            # Search for column-specific sum/average/min/max
            for c in cols:
                if c.lower() in q_lower:
                    safe_c = f'"{c}"'
                    if any(k in q_lower for k in ["average", "mean", "avg"]):
                        res = con.execute(f"SELECT AVG(TRY_CAST({safe_c} AS DOUBLE)) FROM dataset_table").fetchone()[0]
                        if res is not None:
                            return {
                                "answer_text": f"The average value for column '{c}' is {round(res, 2)}.",
                                "sql_used": f"SELECT AVG({c}) FROM dataset_table",
                                "metric_value": round(res, 2)
                            }
                    elif any(k in q_lower for k in ["highest", "maximum", "max", "peak"]):
                        res = con.execute(f"SELECT MAX(TRY_CAST({safe_c} AS DOUBLE)) FROM dataset_table").fetchone()[0]
                        if res is not None:
                            return {
                                "answer_text": f"The maximum value for column '{c}' is {round(res, 2)}.",
                                "sql_used": f"SELECT MAX({c}) FROM dataset_table",
                                "metric_value": round(res, 2)
                            }
                    elif any(k in q_lower for k in ["lowest", "minimum", "min"]):
                        res = con.execute(f"SELECT MIN(TRY_CAST({safe_c} AS DOUBLE)) FROM dataset_table").fetchone()[0]
                        if res is not None:
                            return {
                                "answer_text": f"The minimum value for column '{c}' is {round(res, 2)}.",
                                "sql_used": f"SELECT MIN({c}) FROM dataset_table",
                                "metric_value": round(res, 2)
                            }
                    elif any(k in q_lower for k in ["sum", "total"]):
                        res = con.execute(f"SELECT SUM(TRY_CAST({safe_c} AS DOUBLE)) FROM dataset_table").fetchone()[0]
                        if res is not None:
                            return {
                                "answer_text": f"The sum total for column '{c}' is {round(res, 2)}.",
                                "sql_used": f"SELECT SUM({c}) FROM dataset_table",
                                "metric_value": round(res, 2)
                            }

            return None

data_engine = DataEngineService()
