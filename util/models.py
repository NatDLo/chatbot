from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from util.db import Base
from typing import Optional, Dict
from pydantic import BaseModel

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    vector = Column(JSON, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user = Column(String, nullable=False)
    conversation = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class EmbeddingCreate(BaseModel):
    text: str
    meta: Optional[Dict] = None


class ChatRequest(BaseModel):
    text: str