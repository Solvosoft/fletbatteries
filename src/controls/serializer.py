import json

class SerializerMixin:
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    @classmethod
    def from_json(cls, json_str):
        return cls.from_dict(json.loads(json_str))
