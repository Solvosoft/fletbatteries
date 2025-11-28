from sqlalchemy import Column, Integer, String, Boolean
from data.manager.db_base import Base

class ABC(Base):
    __tablename__ = "abc"  # Nombre de la tabla

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    disabled = Column(Boolean, default=False)