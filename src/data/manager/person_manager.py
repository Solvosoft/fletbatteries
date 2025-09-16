from data.models.person import Person
from data.manager.db_manager import DatabaseManager

class PersonManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create_person(self, name: str, disabled: bool = False, selected: bool = False):
        db = self.dbm.get_session()
        try:
            if db.query(Person).filter(Person.name == name).first():
                raise ValueError("Person already exists")
            person = Person(name=name, disabled=disabled, selected=selected)
            db.add(person)
            db.commit()
            db.refresh(person)
            return person
        finally:
            self.dbm.close_session(db)

    def get_all_persons(self):
        db = self.dbm.get_session()
        try:
            return db.query(Person).all()
        finally:
            self.dbm.close_session(db)

    def get_person_by_id(self, person_id: int):
        db = self.dbm.get_session()
        try:
            return db.query(Person).filter(Person.id == person_id).first()
        finally:
            self.dbm.close_session(db)

    def update_person(self, person_id: int, name: str = None, disabled: bool = None, selected: bool = None):
        db = self.dbm.get_session()
        try:
            person = db.query(Person).filter(Person.id == person_id).first()
            if not person:
                raise ValueError("Person not found")
            if name is not None:
                person.name = name
            if disabled is not None:
                person.disabled = disabled
            if selected is not None:
                person.selected = selected
            db.commit()
            db.refresh(person)
            return person
        finally:
            self.dbm.close_session(db)