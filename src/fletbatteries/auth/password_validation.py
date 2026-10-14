"""
Validación de contraseñas (al estilo de `django.contrib.auth.password_validation`).

    validate_password("1234", user=None)                 # lanza ValidationError
    app = FletBatteriesApp(password_validators=[MinimumLengthValidator(10), NumericPasswordValidator()])

Los validadores se usan al cambiar la contraseña, al recuperarla y en la
administración de usuarios.
"""

import difflib
import re
from typing import Iterable, Optional, Sequence

from fletbatteries.forms.validators import ValidationError
from fletbatteries.i18n import _

# Contraseñas muy comunes (lista corta; una app puede pasar la suya)
COMMON_PASSWORDS = frozenset("""
123456 1234567 12345678 123456789 1234567890 123123 111111 000000 654321 password password1 password123
qwerty qwerty123 abc123 admin admin123 administrator root letmein welcome welcome1 iloveyou monkey dragon
football baseball master shadow sunshine princess passw0rd contraseña contrasena clave secreto 12341234
""".split())


class MinimumLengthValidator:
    def __init__(self, min_length: int = 8):
        self.min_length = min_length

    def validate(self, password: str, user=None):
        if len(password) < self.min_length:
            raise ValidationError(_("This password is too short. It must contain at least {min_length} characters.",
                                    min_length=self.min_length))

    def help_text(self) -> str:
        return _("Your password must contain at least {min_length} characters.", min_length=self.min_length)


class CommonPasswordValidator:
    def __init__(self, passwords: Optional[Iterable[str]] = None):
        self.passwords = frozenset(p.lower() for p in passwords) if passwords is not None else COMMON_PASSWORDS

    def validate(self, password: str, user=None):
        if password.lower().strip() in self.passwords:
            raise ValidationError(_("This password is too common."))

    def help_text(self) -> str:
        return _("Your password can't be a commonly used password.")


class NumericPasswordValidator:
    def validate(self, password: str, user=None):
        if password.isdigit():
            raise ValidationError(_("This password is entirely numeric."))

    def help_text(self) -> str:
        return _("Your password can't be entirely numeric.")


class UserAttributeSimilarityValidator:
    attributes = ("username", "first_name", "last_name", "email")

    def __init__(self, attributes: Optional[Sequence[str]] = None, max_similarity: float = 0.7):
        self.attributes = tuple(attributes or self.attributes)
        self.max_similarity = max_similarity

    def validate(self, password: str, user=None):
        if user is None:
            return
        lowered = password.lower()
        for attr in self.attributes:
            value = user.get(attr) if isinstance(user, dict) else getattr(user, attr, None)
            if not value or not isinstance(value, str):
                continue
            parts = re.split(r"\W+", value.lower()) + [value.lower()]
            for part in parts:
                if len(part) < 3:
                    continue
                if part in lowered or difflib.SequenceMatcher(a=lowered, b=part).quick_ratio() >= self.max_similarity:
                    raise ValidationError(_("The password is too similar to your personal information."))

    def help_text(self) -> str:
        return _("Your password can't be too similar to your other personal information.")


def default_password_validators() -> list:
    return [UserAttributeSimilarityValidator(), MinimumLengthValidator(8), CommonPasswordValidator(),
            NumericPasswordValidator()]


def validate_password(password: str, user=None, validators: Optional[Sequence] = None):
    """Lanza `ValidationError` con todos los problemas de la contraseña."""
    validators = default_password_validators() if validators is None else validators
    errors = []
    for validator in validators:
        try:
            validator.validate(password or "", user)
        except ValidationError as e:
            errors.extend(e.messages)
    if errors:
        raise ValidationError(errors)


def password_help_texts(validators: Optional[Sequence] = None) -> list[str]:
    validators = default_password_validators() if validators is None else validators
    return [v.help_text() for v in validators if hasattr(v, "help_text")]
