from data.manager.country_manager import CountryManager

class CountryControl:
    def __init__(self):
        self.manager = CountryManager()

    def get_all_countries(self):
        return self.manager.get_all_countries()

    def get_country_by_id(self, id: int):
        return self.manager.get_country_by_id(id)

    def create_country(self, name: str, disabled: bool = False, selected: bool = False):
        return self.manager.create_country(name, disabled=disabled, selected=selected)

    def update_country(self, id: int, name: str = None, disabled: bool = None, selected: bool = None):
        return self.manager.update_country(id, name=name, disabled=disabled, selected=selected)