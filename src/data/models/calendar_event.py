import datetime
class Event:
    def __init__(self, id: str, title: str, start_time: datetime.datetime, end_time: datetime.datetime, color: str):
        self.id = id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.color = color

    @classmethod
    def from_json(cls, data: dict):
        """Crea un Event a partir de un diccionario JSON"""
        return cls(
            id=str(data["id"]),
            title=data["title"],
            start_time=datetime.datetime.fromisoformat(data["start_time"]),
            end_time=datetime.datetime.fromisoformat(data["end_time"]),
            color=data.get("color", "green")  
        )