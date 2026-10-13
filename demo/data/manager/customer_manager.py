from fletbatteries.data import BaseManager

from data.models.customer import Customer


class CustomerManager(BaseManager):
    model = Customer
    search_fields = ("name", "last_name", "email", "phone")
    unique_fields = ("email",)
    default_order = "name"
