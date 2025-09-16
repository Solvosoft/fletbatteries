from data.models.country import Country
from data.manager.db_manager import DatabaseManager

class CountryManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create_country(self, name: str, disabled: bool = False, selected: bool = False):
        db = self.dbm.get_session()
        try:
            if db.query(Country).filter(Country.name == name).first():
                raise ValueError("Country already exists")
            country = Country(name=name, disabled=disabled, selected=selected)
            db.add(country)
            db.commit()
            db.refresh(country)
            return country
        finally:
            self.dbm.close_session(db)

    def get_all_countries(self):
        db = self.dbm.get_session()
        try:
            return db.query(Country).all()
        finally:
            self.dbm.close_session(db)

    def get_country_by_id(self, country_id: int):
        db = self.dbm.get_session()
        try:
            return db.query(Country).filter(Country.id == country_id).first()
        finally:
            self.dbm.close_session(db)

    def update_country(self, country_id: int, name: str = None, disabled: bool = None, selected: bool = None):
        db = self.dbm.get_session()
        try:
            country = db.query(Country).filter(Country.id == country_id).first()
            if not country:
                raise ValueError("Country not found")
            if name is not None:
                country.name = name
            if disabled is not None:
                country.disabled = disabled
            if selected is not None:
                country.selected = selected
            db.commit()
            db.refresh(country)
            return country
        finally:
            self.dbm.close_session(db)

