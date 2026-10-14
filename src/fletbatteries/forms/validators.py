"""Errores y validadores reutilizables (al estilo de `django.core.validators`)."""

import ipaddress
import os
import re
from typing import Iterable, Union

from fletbatteries.i18n import _


class ValidationError(ValueError):
    """Error de validación. `messages` es la lista de mensajes para mostrar."""

    def __init__(self, message: Union[str, Iterable[str], dict], **params):
        if isinstance(message, dict):
            self.error_dict = {k: _as_list(v) for k, v in message.items()}
            self.messages = [m for msgs in self.error_dict.values() for m in msgs]
        else:
            self.error_dict = None
            self.messages = [m.format(**params) if params else m for m in _as_list(message)]
        super().__init__("; ".join(self.messages))


def _as_list(value) -> list[str]:
    if isinstance(value, ValidationError):
        return value.messages
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


EMPTY_VALUES = (None, "", [], (), {})


class BaseValidator:
    message = ""
    code = "invalid"

    def __init__(self, limit_value=None, message=None):
        self.limit_value = limit_value
        if message:
            self.message = message

    def __call__(self, value):
        if self.check(value):
            raise ValidationError(self.render_message())

    def render_message(self) -> str:
        return _(self.message, **self.params())

    def params(self) -> dict:
        return {}

    def check(self, value) -> bool:
        """True si `value` es inválido."""
        return False


class MaxLengthValidator(BaseValidator):
    message = "Ensure this value has at most {max_length} characters."

    def params(self):
        return {"max_length": self.limit_value}

    def check(self, value):
        return len(value) > self.limit_value


class MinLengthValidator(BaseValidator):
    message = "Ensure this value has at least {min_length} characters."

    def params(self):
        return {"min_length": self.limit_value}

    def check(self, value):
        return len(value) < self.limit_value


class MaxValueValidator(BaseValidator):
    message = "Ensure this value is less than or equal to {max_value}."

    def params(self):
        return {"max_value": self.limit_value}

    def check(self, value):
        return value > self.limit_value


class MinValueValidator(BaseValidator):
    message = "Ensure this value is greater than or equal to {min_value}."

    def params(self):
        return {"min_value": self.limit_value}

    def check(self, value):
        return value < self.limit_value


class RegexValidator(BaseValidator):
    message = "The value does not match the expected format."

    def __init__(self, regex, message=None, inverse_match=False, flags=0):
        super().__init__(re.compile(regex, flags) if isinstance(regex, str) else regex, message)
        self.inverse_match = inverse_match

    def check(self, value):
        matched = bool(self.limit_value.search(str(value)))
        return matched if self.inverse_match else not matched


class EmailValidator(RegexValidator):
    message = "Enter a valid email address."

    def __init__(self, message=None):
        super().__init__(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message)


class URLValidator(RegexValidator):
    message = "Enter a valid URL."

    def __init__(self, message=None, schemes=("http", "https", "ftp", "ftps")):
        pattern = r"^(?:%s)://[^\s/$.?#][^\s]*$" % "|".join(schemes)
        super().__init__(pattern, message, flags=re.IGNORECASE)


class SlugValidator(RegexValidator):
    message = "Enter a valid slug (letters, numbers, hyphens or underscores)."

    def __init__(self, message=None):
        super().__init__(r"^[-a-zA-Z0-9_]+\Z", message)


class PhoneValidator(RegexValidator):
    """Teléfono con dígitos y separadores comunes (+, espacios, guiones, paréntesis); 7 a 15 dígitos."""

    message = "Enter a valid phone number."

    def __init__(self, message=None, min_digits: int = 7, max_digits: int = 15):
        super().__init__(r"^\+?[\d\s().-]+$", message)
        self.min_digits = min_digits
        self.max_digits = max_digits

    def check(self, value):
        digits = sum(c.isdigit() for c in str(value))
        return super().check(value) or not (self.min_digits <= digits <= self.max_digits)


class IPAddressValidator(BaseValidator):
    message = "Enter a valid IP address."

    def __init__(self, protocol: str = "both", message=None):
        super().__init__(protocol, message)

    def check(self, value):
        try:
            ip = ipaddress.ip_address(str(value).strip())
        except ValueError:
            return True
        return (self.limit_value == "ipv4" and ip.version != 4) or (self.limit_value == "ipv6" and ip.version != 6)


class ProhibitNullCharactersValidator(BaseValidator):
    message = "Null characters are not allowed."

    def check(self, value):
        return "\x00" in str(value)


class MaxFileSizeValidator(BaseValidator):
    """Tamaño máximo de un archivo (`UploadedFile` u objeto con `size`/`path`), en bytes."""

    message = "The file is too large (maximum {max_size})."

    def params(self):
        return {"max_size": human_size(self.limit_value)}

    def check(self, value):
        size = getattr(value, "size", None)
        if size is None and getattr(value, "path", None) and os.path.exists(value.path):
            size = os.path.getsize(value.path)
        if size is None and getattr(value, "content", None) is not None:
            size = len(value.content)
        if getattr(value, "stored", False) and not getattr(value, "is_new", True):
            return False
        return size is not None and size > self.limit_value


def human_size(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return str(size)


validate_email = EmailValidator()
validate_url = URLValidator()
validate_slug = SlugValidator()
validate_ipv46_address = IPAddressValidator()
validate_phone = PhoneValidator()
