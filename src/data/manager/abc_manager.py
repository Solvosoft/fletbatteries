from data.models.abc import ABC
from data.manager.db_manager import DatabaseManager


class ABCManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create(self, name: str, disabled: bool = False):
        """Crear nuevo registro ABC"""
        db = self.dbm.get_session()
        try:
            # Verificar si ya existe
            existing = db.query(ABC).filter(ABC.name == name).first()
            if existing:
                raise ValueError(f"ABC with name '{name}' already exists")

            abc_item = ABC(name=name, disabled=disabled)
            db.add(abc_item)
            db.commit()
            db.refresh(abc_item)
            return abc_item
        except Exception as e:
            db.rollback()
            raise e
        finally:
            self.dbm.close_session(db)

    def get_all(self):
        """Obtener todos los registros ABC"""
        db = self.dbm.get_session()
        try:
            return db.query(ABC).all()
        finally:
            self.dbm.close_session(db)

    def get_by_id(self, item_id: int):
        """Obtener un registro por ID"""
        db = self.dbm.get_session()
        try:
            return db.query(ABC).filter(ABC.id == item_id).first()
        finally:
            self.dbm.close_session(db)

    def update(self, item_id: int, name: str = None, disabled: bool = None):
        """Actualizar registro ABC"""
        db = self.dbm.get_session()
        try:
            abc_item = db.query(ABC).filter(ABC.id == item_id).first()

            if not abc_item:
                raise ValueError("ABC item not found")

            if name is not None:
                # Verificar que el nuevo nombre no exista (excepto para este mismo item)
                existing = db.query(ABC).filter(ABC.name == name, ABC.id != item_id).first()
                if existing:
                    raise ValueError("ABC with this name already exists")
                abc_item.name = name

            if disabled is not None:
                abc_item.disabled = disabled

            db.commit()
            db.refresh(abc_item)
            return abc_item
        except Exception as e:
            db.rollback()
            raise e
        finally:
            self.dbm.close_session(db)

    def delete(self, item_id: int):
        """Eliminar registro ABC"""
        db = self.dbm.get_session()
        try:
            abc_item = db.query(ABC).filter(ABC.id == item_id).first()

            if not abc_item:
                raise ValueError("ABC item not found")

            db.delete(abc_item)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            self.dbm.close_session(db)