from data.models.person import Person
from data.manager.db_manager import DatabaseManager

class PersonManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create(self, name: str, disabled: bool = False):
        db = self.dbm.get_session()
        try:
            if db.query(Person).filter(Person.name == name).first():
                raise ValueError("Person already exists")
            person = Person(name=name, disabled=disabled)
            db.add(person)
            db.commit()
            db.refresh(person)
            return person
        finally:
            self.dbm.close_session(db)

    def get_all(self, eager: bool = False):
        db = self.dbm.get_session()
        try:
            query = db.query(Person)
            return query.all()
        finally:
            self.dbm.close_session(db)

    def get_by_id(self, person_id: int):
        db = self.dbm.get_session()
        try:
            return db.query(Person).filter(Person.id == person_id).first()
        finally:
            self.dbm.close_session(db)

    def update(self, person_id: int, name: str = None, disabled: bool = None):
        db = self.dbm.get_session()
        try:
            person = db.query(Person).filter(Person.id == person_id).first()
            if not person:
                raise ValueError("Person not found")
            if name is not None:
                person.name = name
            if disabled is not None:
                person.disabled = disabled
            db.commit()
            db.refresh(person)
            return person
        finally:
            self.dbm.close_session(db)

    def delete(self, person_id: int):
        db = self.dbm.get_session()
        try:
            person = db.query(Person).filter(Person.id == person_id).first()
            if not person:
                raise ValueError("Person not found")
            db.delete(person)
            db.commit()
            return True
        finally:
            self.dbm.close_session(db)