class AutoCorrectionAgent:
    def execute_remediation(self, df, strategy="MEDIAN"):
        return df.fillna(0)
