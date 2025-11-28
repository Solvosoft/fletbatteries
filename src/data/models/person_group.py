from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from data.manager.db_base import Base

#---------------------------------------
# Intermediate tables
#---------------------------------------
person_group_people = Table(
    "person_group_people",
    Base.metadata,
    Column("person_group_id", ForeignKey("person_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("person_id", ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True),
)

person_group_communities = Table(
    "person_group_communities",
    Base.metadata,
    Column("person_group_id", ForeignKey("person_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("community_id", ForeignKey("communities.id", ondelete="CASCADE"), primary_key=True),
)

class PersonGroup(Base):
    __tablename__ = "person_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    country_id = Column(Integer, ForeignKey("countries.id"))
    country = relationship(
        "Country",
        back_populates="person_groups",
        lazy="joined"
    )

    people = relationship(
        "Person",
        secondary=person_group_people,
        back_populates="person_groups",
        cascade="all",
        passive_deletes=False,
        lazy="joined"
    )

    communities = relationship(
"Community",
        secondary=person_group_communities,
        back_populates="person_groups",
        cascade="all",
        passive_deletes=False,
        lazy="joined"
    )