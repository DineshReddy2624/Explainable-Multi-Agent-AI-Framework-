import pandas as pd

class RuleEngineAgent:
    def __init__(self):
        self.name = "Rule Engine Agent"

    def execute(self, df: pd.DataFrame, rules: list) -> dict:
        violations = []
        for r in rules:
            col = r.get("target_column")
            expr = r.get("expression")
            
            if col in df.columns:
                try:
                    # Example rule expression evaluation: "Age > 18", "Salary > 10000"
                    if ">" in expr:
                        parts = expr.split(">")
                        val = float(parts[1].strip())
                        invalid_mask = df[col] <= val
                        cnt = int(invalid_mask.sum())
                        if cnt > 0:
                            violations.append({
                                "rule_name": r.get("rule_name", expr),
                                "column": col,
                                "expression": expr,
                                "violation_count": cnt
                            })
                except Exception as e:
                    pass

        return {
            "agent": self.name,
            "passed": len(violations) == 0,
            "violations": violations
        }
