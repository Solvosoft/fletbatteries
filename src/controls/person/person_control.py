from data.manager.person_manager import PersonManager

class PersonControl:
    def __init__(self):
        self.manager = PersonManager()

    def get_all_persons(self):
        return self.manager.get_all_persons()

    def get_person_by_id(self, id: int):
        return self.manager.get_person_by_id(id)

    def create_person(self, name: str, disabled: bool = False, selected: bool = False):
        return self.manager.create_person(name, disabled=disabled, selected=selected)

    def update_person(self, id: int, name: str = None, disabled: bool = None, selected: bool = None):
        return self.manager.update_person(id, name=name, disabled=disabled, selected=selected)