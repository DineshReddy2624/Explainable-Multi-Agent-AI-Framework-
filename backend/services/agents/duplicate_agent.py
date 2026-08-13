class DuplicateAgent:
    def detect_duplicates(self, df):
        return int(df.duplicated().sum())
