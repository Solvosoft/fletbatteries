from data.models.product import Product
from data.manager.db_manager import DatabaseManager
from controls.utils import random_image_url

class ProductManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create_product(self, code: str, name: str, price: float, image: str):
        db = self.dbm.get_session()
        try:
            if db.query(Product).filter(Product.code == code).first():
                raise ValueError("Código ya registrado")

            product = Product(code=code, name=name, price=price, image=image)
            db.add(product)
            db.commit()
            db.refresh(product)
            return product
        finally:
            self.dbm.close_session(db)

    def update_product(self, id: int, code: str, name: str, price: float, image: str):
        db = self.dbm.get_session()
        try:
            product = db.query(Product).filter(Product.id == id).first()
            if not product:
                raise ValueError("Producto no encontrado")

            existing = db.query(Product).filter(Product.code == code, Product.id != id).first()
            if existing:
                raise ValueError("Código ya registrado por otro producto")

            product.code = code
            product.name = name
            product.price = price
            product.image = image

            db.commit()
            db.refresh(product)
            return product
        finally:
            self.dbm.close_session(db)

    def get_all_products(self):
        db = self.dbm.get_session()
        try:
            products = db.query(Product).all()
            products_list = [
                {
                    "id": p.id,
                    "code": p.code,
                    "name": p.name,
                    "price": p.price,
                    "image": p.image
                }
                for p in products
            ]
            return products_list
        finally:
            self.dbm.close_session(db)

    def get_product_by_id(self, id: int):
        db = self.dbm.get_session()
        try:
            product = db.query(Product).filter(Product.id == id).first()
            product_dict = {
                "id": product.id,
                "code": product.code,
                "name": product.name,
                "price": product.price,
                "image": product.image
            }
            return product_dict
        finally:
            self.dbm.close_session(db)

    def get_product_by_code(self, code: str):
        db = self.dbm.get_session()
        try:
            return db.query(Product).filter(Product.code == code).first()
        finally:
            self.dbm.close_session(db)

    def delete_product(self, product_id: int):
        db = self.dbm.get_session()
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            db.delete(product)
            db.commit()
            return True
        finally:
            self.dbm.close_session(db)
