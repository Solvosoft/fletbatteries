from src.data.models.customer import Customer
from src.data.manager.db_manager import DatabaseManager

class CustomerManager:
    def __init__(self):
        self.dbm = DatabaseManager()

    def create_customer(self, name: str, phone: str, email: str):
        db = self.dbm.get_session()
        try:
            if db.query(Customer).filter(Customer.email == email).first():
                raise ValueError("Email ya registrado")

            customer = Customer(name=name, phone=phone, email=email)
            db.add(customer)
            db.commit()
            db.refresh(customer)
            return customer
        finally:
            self.dbm.close_session(db)

    def get_customer_by_email(self, email: str):
        db = self.dbm.get_session()
        try:
            return db.query(Customer).filter(Customer.email == email).first()
        finally:
            self.dbm.close_session(db)

    def get_all_customers(self):
        db = self.dbm.get_session()
        try:
            return db.query(Customer).all()
        finally:
            self.dbm.close_session(db)

    def delete_customer(self, customer_id: int):
        db = self.dbm.get_session()
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return False
            db.delete(customer)
            db.commit()
            return True
        finally:
            self.dbm.close_session(db)
