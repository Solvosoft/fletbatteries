"""
Traducciones de los textos del framework.

Los textos se escriben en inglés en el código (`_("Save")`) y se traducen con
el catálogo del idioma activo. El idioma por defecto es español y se cambia con
`set_default_language("en")`. Una app puede agregar o sobrescribir
traducciones con `add_translations("es", {...})`.

Idioma por sesión: `set_language("en", page)` (o sin `page` dentro de un
handler de Flet) cambia el idioma solo de esa sesión; `_()` lo toma de la
página activa (`ft.context.page`) y, si no hay, usa el idioma por defecto.

Los textos que se evalúan al definir una clase (p. ej. `title = _("Users")`)
se traducen una sola vez, con el idioma por defecto.

Formatos de fecha por idioma: `get_format("date" | "time" | "datetime")`.
"""

from string import Formatter
from typing import Optional

from fletbatteries.i18n import es

SESSION_LANGUAGE_KEY = "fletbatteries.language"

_catalogs: dict[str, dict[str, str]] = {"en": {}, "es": dict(es.MESSAGES)}
_default_language = "es"

# Formatos de fecha/hora (strftime) por idioma
_formats: dict[str, dict[str, str]] = {
    "es": {"date": "%d/%m/%Y", "time": "%H:%M", "datetime": "%d/%m/%Y %H:%M"},
    "en": {"date": "%m/%d/%Y", "time": "%H:%M", "datetime": "%m/%d/%Y %H:%M"},
}


def _current_page():
    try:
        import flet as ft

        return ft.context.page
    except (RuntimeError, ImportError, AttributeError):
        return None


def _session_language(page=None) -> Optional[str]:
    page = page or _current_page()
    if page is None:
        return None
    try:
        return page.session.store.get(SESSION_LANGUAGE_KEY)
    except (AttributeError, RuntimeError):
        return None


def set_default_language(language: str):
    """Idioma de todo el proceso (lo usan las sesiones que no eligieron otro)."""
    global _default_language
    _catalogs.setdefault(language, {})
    _default_language = language


def get_default_language() -> str:
    return _default_language


def set_language(language: str, page=None):
    """
    Cambia el idioma de la sesión de `page` (o de la página activa). Fuera de
    una sesión de Flet cambia el idioma por defecto.
    """
    _catalogs.setdefault(language, {})
    page = page or _current_page()
    if page is None:
        set_default_language(language)
        return
    page.session.store.set(SESSION_LANGUAGE_KEY, language)


def get_language(page=None) -> str:
    return _session_language(page) or _default_language


def available_languages() -> list[str]:
    return list(_catalogs)


def add_translations(language: str, messages: dict[str, str]):
    _catalogs.setdefault(language, {}).update(messages)


def _interpolate(text: str, kwargs: dict) -> str:
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text


def gettext(message: str, **kwargs) -> str:
    """Traduce `message`; si recibe kwargs los interpola con `str.format`."""
    text = _catalogs.get(get_language(), {}).get(message, message)
    return _interpolate(text, kwargs)


_ = gettext


def ngettext(singular: str, plural: str, n: int, **kwargs) -> str:
    """
    Traducción con plural: usa `singular` si `n == 1` y `plural` en otro caso.
    `n` también está disponible para interpolar (`"{n} records"`).
    """
    message = singular if n == 1 else plural
    text = _catalogs.get(get_language(), {}).get(message, message)
    return _interpolate(text, {"n": n, **kwargs})


def add_formats(language: str, formats: dict[str, str]):
    """Define o cambia los formatos `date`, `time` y `datetime` de un idioma."""
    _formats.setdefault(language, {}).update(formats)


def get_format(kind: str, language: Optional[str] = None) -> str:
    """Formato strftime de `kind` ("date", "time", "datetime") para el idioma activo."""
    language = language or get_language()
    formats = _formats.get(language) or _formats["es"]
    return formats.get(kind) or _formats["es"][kind]


def placeholders(message: str) -> set[str]:
    return {name for _lit, name, _spec, _conv in Formatter().parse(message) if name}


__all__ = [
    "_",
    "gettext",
    "ngettext",
    "set_language",
    "get_language",
    "set_default_language",
    "get_default_language",
    "available_languages",
    "add_translations",
    "add_formats",
    "get_format",
]
