"""
Mapas (equivalentes a `MapPointInput` / `DJMap` de djgentelella). Requieren el
extra `fletbatteries[maps]` (flet-map) y conexión para descargar los mosaicos.

- `MapPointInput`: elegir un punto con un clic. El valor es el texto "lat,lng".
- `MapView`: mapa de solo lectura con marcadores.
"""

from typing import Optional, Sequence

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.widgets.base import LabeledWidget

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
DEFAULT_CENTER = (9.9325, -84.0796)  # San José, Costa Rica


def parse_point(value) -> Optional[tuple[float, float]]:
    """Convierte "lat,lng" (o una tupla) en `(lat, lng)`; `None` si no es válido."""
    if value in (None, ""):
        return None
    try:
        if isinstance(value, str):
            lat, lng = (float(v) for v in value.split(","))
        else:
            lat, lng = float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return lat, lng


def format_point(point) -> str:
    return f"{point[0]:.6f},{point[1]:.6f}" if point else ""


def _marker(point, color=ft.Colors.RED, title: Optional[str] = None):
    import flet_map as fm

    return fm.Marker(
        content=ft.Icon(ft.Icons.LOCATION_ON, color=color, size=36, tooltip=title),
        coordinates=fm.MapLatitudeLongitude(point[0], point[1]),
        width=36,
        height=36,
    )


def _base_map(center, zoom, layers, on_tap=None, height=300):
    import flet_map as fm

    return fm.Map(
        initial_center=fm.MapLatitudeLongitude(*center),
        initial_zoom=zoom,
        layers=[fm.TileLayer(url_template=TILE_URL, user_agent_package_name="fletbatteries"), *layers],
        on_tap=on_tap,
        height=height,
        expand=False,
    )


class MapPointInput(LabeledWidget):
    def __init__(self, label=None, help_text=None, center=DEFAULT_CENTER, zoom: float = 12, height: int = 300,
                 **kwargs):
        import flet_map as fm

        self._point: Optional[tuple[float, float]] = None
        self.marker_layer = fm.MarkerLayer(markers=[])
        self.map = _base_map(center, zoom, [self.marker_layer], on_tap=self._on_tap, height=height)
        self.lat_field = ft.TextField(label=_("Latitude"), dense=True, expand=True, on_change=self._on_text)
        self.lng_field = ft.TextField(label=_("Longitude"), dense=True, expand=True, on_change=self._on_text)
        body = ft.Column([ft.Container(self.map, height=height, border_radius=8,
                                       clip_behavior=ft.ClipBehavior.HARD_EDGE),
                          ft.Row([self.lat_field, self.lng_field])], spacing=6, tight=True)
        super().__init__(body, label=label, help_text=help_text, **kwargs)

    def _on_tap(self, e):
        self.set_value((e.coordinates.latitude, e.coordinates.longitude))
        self.refresh()
        self.changed(e)

    def _on_text(self, e):
        point = parse_point(f"{self.lat_field.value},{self.lng_field.value}")
        self._point = point
        self._sync_marker()
        self.refresh()
        self.changed(e)

    def _sync_marker(self):
        self.marker_layer.markers = [_marker(self._point)] if self._point else []

    def get_value(self) -> str:
        if self._point is None and (self.lat_field.value or self.lng_field.value):
            return f"{self.lat_field.value},{self.lng_field.value}"  # inválido: lo valida el campo
        return format_point(self._point)

    def set_value(self, value):
        self._point = parse_point(value)
        self.lat_field.value = f"{self._point[0]:.6f}" if self._point else ""
        self.lng_field.value = f"{self._point[1]:.6f}" if self._point else ""
        self._sync_marker()


class MapView(ft.Container):
    """Mapa con marcadores: `points` es una lista de dicts con `lat`, `lng`, `title` y `color` opcionales."""

    def __init__(self, points: Sequence[dict] = (), center=None, zoom: float = 7, height: int = 400, **kwargs):
        import flet_map as fm

        super().__init__(height=height, border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE, **kwargs)
        self.marker_layer = fm.MarkerLayer(markers=[])
        self.set_points(points)
        if center is None and self.points:
            center = (sum(p["lat"] for p in self.points) / len(self.points),
                      sum(p["lng"] for p in self.points) / len(self.points))
        self.content = _base_map(center or DEFAULT_CENTER, zoom, [self.marker_layer], height=height)

    def set_points(self, points: Sequence[dict]):
        self.points = [p for p in points if parse_point((p.get("lat"), p.get("lng")))]
        self.marker_layer.markers = [
            _marker((p["lat"], p["lng"]), p.get("color", ft.Colors.RED), p.get("title")) for p in self.points
        ]
