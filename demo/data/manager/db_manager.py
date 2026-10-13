import settings
from data.manager.db_base import Base


class DatabaseManager:
    """Crear, reiniciar o actualizar el esquema de la base de datos de la demo."""

    def __init__(self):
        self.db = settings.DATABASE
        self.engine = self.db.engine

    def get_session(self):
        return self.db.SessionLocal()

    def close_session(self, db):
        db.close()

    def create_db(self):
        Base.metadata.create_all(bind=self.engine)
        print("Database created.")

    def reset_db(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        print("Database reset.")

    def update_schema(self):
        Base.metadata.create_all(bind=self.engine)
        print("Schema updated.")
