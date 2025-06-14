from sqlalchemy import Boolean, Column, Integer, UUID, String
import uuid
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String)
    password = Column(String)
    is_active = Column(Boolean, default=True)