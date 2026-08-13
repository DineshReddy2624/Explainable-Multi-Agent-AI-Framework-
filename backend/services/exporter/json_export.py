def export_to_json(df, output_path: str):
    df.to_json(output_path, orient="records")
    return output_path
