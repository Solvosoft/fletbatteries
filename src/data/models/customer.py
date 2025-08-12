from sqlalchemy import Column, Integer, String
# Base declarative
from data.manager.db_base import Base
from controls.serializer import SerializerMixin

class Customer(Base, SerializerMixin):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String, unique=True, nullable=False)
    last_name = Column(String)
