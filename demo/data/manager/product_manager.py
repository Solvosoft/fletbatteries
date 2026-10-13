from fletbatteries.data import BaseManager

from data.models.product import Product


class ProductManager(BaseManager):
    model = Product
    search_fields = ("code", "name")
    unique_fields = ("code",)
    default_order = "name"
