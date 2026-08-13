def get_dataset_summary(df):
    return {
        "row_count": len(df),
        "col_count": len(df.columns),
        "columns": list(df.columns)
    }
