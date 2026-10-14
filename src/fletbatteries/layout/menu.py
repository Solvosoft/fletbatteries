"""Menú declarativo con permisos (equivalente a `MenuItem` de djgentelella)."""

import dataclasses
from typing import Any, Callable, Optional, Sequence

from fletbatteries.auth.session import has_perms


@dataclasses.dataclass
class MenuItem:
    title: str
    route: Optional[str] = None
    icon: Any = None
    perms: Sequence[str] = ()
    children: list = dataclasses.field(default_factory=list)
    position: str = "sidebar"  # "sidebar" | "top" | "footer"
    any_perm: bool = False
    # badge(page) -> número o texto que se muestra sobre el ícono (None/0 = sin badge)
    badge: Optional[Callable[[Any], Any]] = None

    def badge_value(self, page) -> Optional[str]:
        if self.badge is None:
            return None
        try:
            value = self.badge(page)
        except Exception:  # noqa: BLE001 - un badge roto no debe romper el menú
            import logging

            logging.getLogger(__name__).exception("Error calculando el badge de %s", self.title)
            return None
        return None if value in (None, 0, "", False) else str(value)

    def visible_for(self, page) -> bool:
        return has_perms(page, self.perms, any_perm=self.any_perm)


def filter_menu(items: Sequence[MenuItem], page) -> list[MenuItem]:
    """Quita lo que el usuario no puede ver (y los grupos que quedan vacíos)."""
    result = []
    for item in items:
        if not item.visible_for(page):
            continue
        children = filter_menu(item.children, page)
        if item.children and not children and not item.route:
            continue
        result.append(dataclasses.replace(item, children=children))
    return result


def flatten(items: Sequence[MenuItem]) -> list[MenuItem]:
    result = []
    for item in items:
        result.append(item)
        result.extend(flatten(item.children))
    return result
