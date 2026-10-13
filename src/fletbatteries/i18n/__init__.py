"""
Traducciones de los textos del framework.

Los textos se escriben en inglés en el código (`_("Save")`) y se traducen con
el catálogo del idioma activo. El idioma por defecto es español; se cambia con
`set_language("en")`. Una app puede agregar o sobrescribir traducciones con
`add_translations("es", {...})`.
"""

from string import Formatter

from fletbatteries.i18n import es

_catalogs: dict[str, dict[str, str]] = {"en": {}, "es": dict(es.MESSAGES)}
_language = "es"


def set_language(language: str):
    global _language
    _catalogs.setdefault(language, {})
    _language = language


def get_language() -> str:
    return _language


def add_translations(language: str, messages: dict[str, str]):
    _catalogs.setdefault(language, {}).update(messages)


def gettext(message: str, **kwargs) -> str:
    """Traduce `message`; si recibe kwargs los interpola con `str.format`."""
    text = _catalogs.get(_language, {}).get(message, message)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


_ = gettext


def placeholders(message: str) -> set[str]:
    return {name for _lit, name, _spec, _conv in Formatter().parse(message) if name}


__all__ = ["_", "gettext", "set_language", "get_language", "add_translations"]
