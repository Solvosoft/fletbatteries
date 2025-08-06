from src.data.models.user import User
from src.controls.encrypt import hash_password, verify_password
from src.data.manager.db_manager import DatabaseManager

class UserManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    # Crear usuario
    def create_user(self, name: str, email: str, password: str):
        db = self.dbm.get_session()
        try:
            if db.query(User).filter(User.email == email).first():
                raise ValueError("Email ya registrado")

            hashed = hash_password(password)
            user = User(name=name, email=email, password=hashed)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            self.dbm.close_session(db)

    # Autenticar usuario
    def login_user(self, email: str, password: str):
        db = self.dbm.get_session()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user or not verify_password(password, user.password_hash):
                return None
            return user
        finally:
            self.dbm.close_session(db)

    # Leer por ID
    def get_user_by_id(self, user_id: int):
        db = self.dbm.get_session()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            self.dbm.close_session(db)

    # Leer por email
    def get_user_by_email(self, email: str):
        db = self.dbm.get_session()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            self.dbm.close_session(db)

    # Eliminar usuario
    def delete_user(self, user_id: int):
        db = self.dbm.get_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            db.delete(user)
            db.commit()
            return True
        finally:
            self.dbm.close_session(db)
