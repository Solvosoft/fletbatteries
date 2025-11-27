from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Base declarative
from data.manager.db_base import Base

class DatabaseManager:
    def __init__(self):
        # Agregar el nombre de la base de datos
        self.db_url = f"sqlite:///template.db"
        self.engine = create_engine(
            self.db_url,
            # necesario para SQLite
            connect_args={"check_same_thread": False}
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_session(self) -> Session:
        """Abre una nueva sesión de base de datos"""
        try:
            db = self.SessionLocal()
            return db
        except SQLAlchemyError as e:
            print(f"Error al abrir la sesión: {e}")
            return None

    def close_session(self, db: Session):
        """Cierra una sesión"""
        try:
            db.close()
        except SQLAlchemyError as e:
            print(f"Error al cerrar la sesión: {e}")

    def create_db(self):
        """Crea las tablas si no existen"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Base de datos creada.")
        except SQLAlchemyError as e:
            print(f"Error al crear la base de datos: {e}")

    def reset_db(self):
        """Elimina todas las tablas y las vuelve a crear"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            print("Base de datos reseteada.")
        except SQLAlchemyError as e:
            print(f"Error al resetear la base de datos: {e}")

    def update_schema(self):
        """Actualiza el esquema (crea tablas faltantes)"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Esquema actualizado.")
        except SQLAlchemyError as e:
            print(f"Error al actualizar esquema: {e}")
