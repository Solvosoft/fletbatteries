from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from data.manager.db_base import Base

class DatabaseManager:
    def __init__(self):
        # Database URL
        self.db_url = f"sqlite:///template.db"
        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False}  # Required for SQLite
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_session(self) -> Session:
        """Open a new database session"""
        try:
            db = self.SessionLocal()
            return db
        except SQLAlchemyError as e:
            print(f"Error opening session: {e}")
            return None

    def close_session(self, db: Session):
        """Close a database session"""
        try:
            db.close()
        except SQLAlchemyError as e:
            print(f"Error closing session: {e}")

    def create_db(self):
        """Create tables if they do not exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Database created.")
        except SQLAlchemyError as e:
            print(f"Error creating database: {e}")

    def reset_db(self):
        """Drop all tables and recreate them"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            print("Database reset.")
        except SQLAlchemyError as e:
            print(f"Error resetting database: {e}")

    def update_schema(self):
        """Update schema by creating missing tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Schema updated.")
        except SQLAlchemyError as e:
            print(f"Error updating schema: {e}")