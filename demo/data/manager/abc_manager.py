from fletbatteries.data import BaseManager

from data.models.abc import ABC


class ABCManager(BaseManager):
    model = ABC
    search_fields = ("name",)
    unique_fields = ("name",)
