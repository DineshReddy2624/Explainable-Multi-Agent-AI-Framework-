import os
import pandas as pd
from core.config import settings

class ExportAgent:
    def __init__(self):
        self.name = "Export Agent"

    def export(self, df: pd.DataFrame, dataset_id: int, file_format: str = "csv") -> str:
        os.makedirs(settings.CLEANED_DIR, exist_ok=True)
        filename = f"cleaned_dataset_{dataset_id}.{file_format.lower()}"
        out_path = os.path.join(settings.CLEANED_DIR, filename)

        if file_format.lower() == "csv":
            df.to_csv(out_path, index=False)
        elif file_format.lower() == "excel" or file_format.lower() == "xlsx":
            df.to_excel(out_path, index=False)
        elif file_format.lower() == "json":
            df.to_json(out_path, orient="records")
        else:
            df.to_csv(out_path, index=False)

        return out_path
