from fletbatteries.data import BaseManager

from controls.encrypt import hash_password
from data.models.user import User


class UserManager(BaseManager):
    model = User
    search_fields = ("name", "email")
    unique_fields = ("email",)

    def before_save(self, s, obj, data, created):
        # La contraseña se guarda con hash; vacía al editar = no cambiarla
        password = data.get("password")
        if password:
            data["password"] = hash_password(password)
        else:
            data.pop("password", None)
