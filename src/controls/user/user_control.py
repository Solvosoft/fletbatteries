
from data.manager.user_manager import UserManager

class UserControl:
    def __init__(self):
        self.manager = UserManager()

    def get_all_users(self):
        return self.manager.get_all_users()

    def create_user(self, name, email, password):
        return self.manager.create_user(name, email, password)

    def update_user(self, user_id, name, email, password):
        return self.manager.update_user(user_id, name, email, password)

    def delete_user(self, user_id):
        return self.manager.delete_user(user_id)