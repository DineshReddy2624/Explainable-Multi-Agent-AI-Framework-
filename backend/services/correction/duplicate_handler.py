class DuplicateHandler:
    def handle(self, df):
        return df.drop_duplicates()
