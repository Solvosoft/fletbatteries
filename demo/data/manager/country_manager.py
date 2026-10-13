from fletbatteries.data import BaseManager

from data.models.country import Country


class CountryManager(BaseManager):
    model = Country
    search_fields = ("name",)
    unique_fields = ("name",)
    default_order = "name"
