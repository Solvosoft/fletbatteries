from fletbatteries.data import BaseManager

from data.models.person import Person


class PersonManager(BaseManager):
    model = Person
    search_fields = ("name",)
    unique_fields = ("name",)
