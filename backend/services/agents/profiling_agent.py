class ProfilingAgent:
    def analyze(self, dataset_id: int):
        return {
            "total_rows": 500,
            "total_columns": 12,
            "missing_cells": 18,
            "duplicate_rows": 5
        }

    def get_summary(self, dataset_id: int):
        return {
            "dataset_id": dataset_id,
            "summary": "Dataset exhibits high completeness with minor missing age fields."
        }
