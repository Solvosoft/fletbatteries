
from data.manager.customer_manager import CustomerManager

class CustomerControl:
    def __init__(self):
        self.manager = CustomerManager()

    def get_all_customers(self):
        return self.manager.get_all_customers()

    def get_customer_by_email(self, email):
        return self.manager.get_customer_by_email(email)

    def create_customer(self, name, last_name, phone, email):
        return self.manager.create_customer(name, last_name, phone, email)

    def delete_customer(self, customer_id):
        return self.manager.delete_customer(customer_id)

    def update_customer(self, customer_id, name, last_name, phone, email):
        return self.manager.update_customer(customer_id, name, last_name, phone, email)