from sqlalchemy import Column, Integer, String
# Base declarative
from data.manager.db_base import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String, unique=True, nullable=False)
