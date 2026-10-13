import datetime

from sqlalchemy import Column, DateTime, Integer, String

from data.manager.db_base import Base


class Event(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    color = Column(String, nullable=False, default="green")
    description = Column(String, nullable=False, default="")
    location = Column(String, nullable=False, default="")

    @classmethod
    def from_json(cls, data: dict):
        """Crea un Event a partir de un diccionario JSON"""
        start_time = data["start_time"]
        end_time = data["end_time"]
        return cls(
            id=int(data["id"]) if data.get("id") is not None else None,
            title=data["title"],
            start_time=start_time if isinstance(start_time, datetime.datetime) else datetime.datetime.fromisoformat(start_time),
            end_time=end_time if isinstance(end_time, datetime.datetime) else datetime.datetime.fromisoformat(end_time),
            color=data.get("color", "green"),
            description=data.get("description", ""),
            location=data.get("location", ""),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "color": self.color,
            "description": self.description,
            "location": self.location,
        }
