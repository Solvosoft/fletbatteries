from sqlalchemy import Column, Integer, String, Boolean
from data.manager.db_base import Base
from sqlalchemy.orm import relationship
from data.models.person_group import PersonGroup

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    disabled = Column(Boolean, default=False)

    person_groups = relationship("PersonGroup", back_populates="country")