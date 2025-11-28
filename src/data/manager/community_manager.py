from data.models.community import Community
from data.manager.db_manager import DatabaseManager

class CommunityManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create(self, name: str, disabled: bool = False):
        db = self.dbm.get_session()
        try:
            if db.query(Community).filter(Community.name == name).first():
                raise ValueError("Community already exists")
            community = Community(name=name, disabled=disabled)
            db.add(community)
            db.commit()
            db.refresh(community)
            return community
        finally:
            self.dbm.close_session(db)

    def get_all(self):
        db = self.dbm.get_session()
        try:
            return db.query(Community).all()
        finally:
            self.dbm.close_session(db)

    def get_by_id(self, community_id: int):
        db = self.dbm.get_session()
        try:
            return db.query(Community).filter(Community.id == community_id).first()
        finally:
            self.dbm.close_session(db)

    def update(self, community_id: int, name: str = None, disabled: bool = None):
        db = self.dbm.get_session()
        try:
            community = db.query(Community).filter(Community.id == community_id).first()
            if not community:
                raise ValueError("Community not found")
            if name is not None:
                community.name = name
            if disabled is not None:
                community.disabled = disabled
            db.commit()
            db.refresh(community)
            return community
        finally:
            self.dbm.close_session(db)

    def delete(self, community_id: int):
        db = self.dbm.get_session()
        try:
            community = db.query(Community).filter(Community.id == community_id).first()
            if not community:
                raise ValueError("Community not found")
            db.delete(community)
            db.commit()
            return True
        finally:
            self.dbm.close_session(db)