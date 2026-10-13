"""Menú declarativo con permisos (equivalente a `MenuItem` de djgentelella)."""

import dataclasses
from typing import Any, Optional, Sequence

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
