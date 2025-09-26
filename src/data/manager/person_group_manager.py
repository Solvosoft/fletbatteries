from data.models.person_group import PersonGroup
from data.models.person import Person
from data.models.community import Community
from data.models.country import Country
from data.manager.db_manager import DatabaseManager
from sqlalchemy.orm import joinedload

class PersonGroupManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create(self, name: str, country_id: int, people_ids=None, community_ids=None):
        db = self.dbm.get_session()
        try:
            if db.query(PersonGroup).filter(PersonGroup.name == name).first():
                raise ValueError("PersonGroup already exists")

            group = PersonGroup(name=name, country_id=country_id)

            if people_ids:
                people = db.query(Person).filter(Person.id.in_(people_ids)).all()
                group.people = people

            if community_ids:
                communities = db.query(Community).filter(Community.id.in_(community_ids)).all()
                group.communities = communities

            db.add(group)
            db.commit()
            db.refresh(group)
            return group
        finally:
            self.dbm.close_session(db)

    def get_all(self, eager: bool = False):
        db = self.dbm.get_session()
        try:
            query = db.query(PersonGroup)
            if eager:
                query = query.options(
                    joinedload(PersonGroup.people),
                    joinedload(PersonGroup.communities),
                    joinedload(PersonGroup.country)
                )
            return query.all()
        finally:
            self.dbm.close_session(db)

    def get_by_id(self, group_id: int):
        db = self.dbm.get_session()
        try:
            return db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
        finally:
            self.dbm.close_session(db)

    def update(self, group_id: int, name: str = None, country_id: int = None,
                            people_ids=None, community_ids=None):
        db = self.dbm.get_session()
        try:
            group = db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
            if not group:
                raise ValueError("PersonGroup not found")

            if name is not None:
                group.name = name
            if country_id is not None:
                group.country_id = country_id
            if people_ids is not None:
                people = db.query(Person).filter(Person.id.in_(people_ids)).all()
                group.people = people
            if community_ids is not None:
                communities = db.query(Community).filter(Community.id.in_(community_ids)).all()
                group.communities = communities

            db.commit()
            db.refresh(group)
            return group
        finally:
            self.dbm.close_session(db)

    def delete(self, group_id: int):
        db = self.dbm.get_session()
        try:
            group = db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
            if not group:
                raise ValueError("PersonGroup not found")
            db.delete(group)
            db.commit()
            return True
        finally:
            self.dbm.close_session(db)