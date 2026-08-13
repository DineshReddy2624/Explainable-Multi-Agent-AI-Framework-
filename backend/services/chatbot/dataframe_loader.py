class DataFrameLoader:
    def load_df(self, df):
        return df.to_dict(orient="records")
