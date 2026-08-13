from sqlalchemy import Column, Integer, String, Boolean, JSON
from core.database import Base

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String, nullable=False)
    target_column = Column(String, nullable=False)
    expression = Column(String, nullable=False) # e.g. Age > 18, Salary > 10000
    parameters = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
