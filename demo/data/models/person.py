from sqlalchemy import Column, Integer, String, Boolean
from data.manager.db_base import Base
from sqlalchemy.orm import relationship
from data.models.person_group import PersonGroup

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    disabled = Column(Boolean, default=False)

    person_groups = relationship("PersonGroup", secondary="person_group_people", back_populates="people")