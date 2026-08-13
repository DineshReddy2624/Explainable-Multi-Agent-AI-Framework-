class MissingHandler:
    def handle(self, df, strategy="mean"):
        return df.fillna(0)
