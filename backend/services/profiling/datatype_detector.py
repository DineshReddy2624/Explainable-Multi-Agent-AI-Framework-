def detect_datatypes(df):
    return {col: str(dtype) for col, dtype in df.dtypes.items()}
