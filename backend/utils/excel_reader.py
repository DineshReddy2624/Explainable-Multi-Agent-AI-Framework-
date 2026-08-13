import pandas as pd

def read_excel_file(file_path: str) -> pd.DataFrame:
    return pd.read_excel(file_path)
