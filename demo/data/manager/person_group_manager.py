from fletbatteries.data import BaseManager

from data.models.person_group import PersonGroup


class PersonGroupManager(BaseManager):
    model = PersonGroup
    search_fields = ("name",)
    unique_fields = ("name",)
