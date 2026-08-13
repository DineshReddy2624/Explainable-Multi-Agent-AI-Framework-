import pandas as pd

def read_csv_file(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)
