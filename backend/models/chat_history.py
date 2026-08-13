from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from datetime import datetime
from core.database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"), nullable=False)
    user_query = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    source_rows = Column(Text, nullable=True) # JSON list of retrieved context rows
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
