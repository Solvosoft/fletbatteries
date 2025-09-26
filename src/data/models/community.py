from sqlalchemy import Column, Integer, String, Boolean
from data.manager.db_base import Base
from sqlalchemy.orm import relationship
from data.models.person_group import PersonGroup

class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    disabled = Column(Boolean, default=False)

    person_groups = relationship("PersonGroup", secondary="person_group_communities", back_populates="communities")