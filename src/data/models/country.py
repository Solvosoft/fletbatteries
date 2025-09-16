from sqlalchemy import Column, Integer, String, Boolean
from data.manager.db_base import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    disabled = Column(Boolean, default=False)
    selected = Column(Boolean, default=False)
