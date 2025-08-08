
from data.manager.product_manager import ProductManager

class ProductControl:
    def __init__(self):
        self.manager = ProductManager()

    def get_all_products(self):
        return self.manager.get_all_products()

    def get_product_by_id(self, id):
        return self.manager.get_product_by_id(id)

    def create_product(self, name, code, price, image):
        return self.manager.create_product(code, name, price, image)

    def update_product(self, id, name, code, price, image):
        return self.manager.update_product(id, code, name, price, image)

    def delete_product(self, id):
        return self.manager.delete_product(id)