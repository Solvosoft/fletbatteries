"""
Recuperación de contraseña con un código enviado por correo.

    service = PasswordResetService()
    service.request_reset("ana@example.com")              # envía un código de 6 dígitos
    service.confirm_reset("ana@example.com", "123456", "nueva-clave-segura")

Funciona igual en escritorio, web y móvil: el usuario escribe el código en la
app. Para no revelar qué usuarios existen, `request_reset` no informa si el
usuario o el correo existen. El código vence en `expires_minutes` y admite
`max_attempts` intentos.
"""

import datetime
import hashlib
import hmac
import secrets
from typing import Optional, Sequence

import sqlalchemy as sa

from fletbatteries.auth.models import PasswordReset
from fletbatteries.data.manager import BaseManager
from fletbatteries.forms.validators import ValidationError
from fletbatteries.i18n import _


class PasswordResetManager(BaseManager):
    model = PasswordReset
    default_order = "-created_at"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class PasswordResetService:
    def __init__(self, user_manager=None, expires_minutes: int = 15, max_attempts: int = 5,
                 code_length: int = 6, validators: Optional[Sequence] = None, app_name: str = ""):
        from fletbatteries.auth.backend import UserManager

        self.users = user_manager or UserManager()
        self.resets = PasswordResetManager()
        self.expires_minutes = expires_minutes
        self.max_attempts = max_attempts
        self.code_length = code_length
        self.validators = validators
        self.app_name = app_name

    def generate_code(self) -> str:
        return "".join(secrets.choice("0123456789") for _i in range(self.code_length))

    def email_content(self, user, code: str) -> tuple[str, str]:
        """Asunto y cuerpo del correo (se puede sobrescribir)."""
        subject = _("Password reset code") + (f" - {self.app_name}" if self.app_name else "")
        body = _("Hello {name},\n\nYour code to reset the password is: {code}\n\nIt expires in {minutes} minutes. "
                 "If you did not request it, ignore this message.",
                 name=user.first_name or user.username, code=code, minutes=self.expires_minutes)
        return subject, body

    def request_reset(self, identifier: str) -> Optional[str]:
        """
        Crea un código y lo envía al correo del usuario (por nombre de usuario o
        correo). Devuelve el código (para pruebas) o `None` si no se envió.
        """
        from fletbatteries.contrib.email import send_mail

        user = self.users.get_by_username_or_email(identifier)
        if user is None or not user.is_active or not user.email:
            return None
        code = self.generate_code()
        now = datetime.datetime.now()
        with self.resets.session() as s:
            # Solo vale el último código
            s.execute(sa.update(PasswordReset).where(PasswordReset.user_id == user.id,
                                                     PasswordReset.used_at.is_(None)).values(used_at=now))
        self.resets.create(user_id=user.id, code_hash=_hash_code(code),
                           expires_at=now + datetime.timedelta(minutes=self.expires_minutes))
        subject, body = self.email_content(user, code)
        send_mail(user.email, subject, body)
        return code

    def confirm_reset(self, identifier: str, code: str, new_password: str, confirm: Optional[str] = None):
        """Cambia la contraseña si el código es válido; si no, lanza `ValidationError({campo: msgs})`."""
        from fletbatteries.auth.backend import LoginAttemptManager
        from fletbatteries.auth.password_validation import validate_password

        invalid = ValidationError({"code": [_("The code is invalid or has expired.")]})
        user = self.users.get_by_username_or_email(identifier)
        if user is None:
            raise invalid
        reset = self.resets.first(user_id=user.id, used_at__isnull=True)
        if reset is None or reset.expires_at < datetime.datetime.now() or reset.attempts >= self.max_attempts:
            raise invalid
        if not hmac.compare_digest(reset.code_hash, _hash_code((code or "").strip())):
            self.resets.update(reset.id, attempts=reset.attempts + 1)
            raise invalid
        if confirm is not None and confirm != new_password:
            raise ValidationError({"confirm": [_("The two password fields didn't match.")]})
        try:
            validate_password(new_password, user, self.validators)
        except ValidationError as e:
            raise ValidationError({"new_password": e.messages})
        self.users.set_password(user.id, new_password)
        self.resets.update(reset.id, used_at=datetime.datetime.now())
        LoginAttemptManager().clear_failures(user.username)
        return True
