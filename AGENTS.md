# Guía para agentes

FletBatteries es una app Flet **1.0.4** (Python 3.13, entorno gestionado con `uv`). El código fuente está en `src/` y se ejecuta con `src/` en el `PYTHONPATH`. Por eso los imports son `from components...`, `from views...`, etc.

## Comandos

```bash
make setup                 # primera vez: recrea .venv, instala dependencias y crea las tablas
make sync                  # actualizar .venv después de cambiar pyproject.toml / uv.lock
make test                  # pruebas headless (siempre antes de terminar un cambio)
make test PYTEST_ARGS="-k calendar -x"
make screenshots ROUTES="/calendar"   # revisión visual: screenshots/calendar.png
make lint
```

Para agregar una dependencia usa `uv add <paquete>` (o `uv add --dev <paquete>`) y luego `make requirements`.

## Cómo verificar un cambio

1. **Pruebas automáticas (`make test`)**. Son deterministas y no dependen de un agente: si pasan, el cambio funciona.
   - `tests/harness.py` (`AppHarness`) ejecuta el `main(page)` real contra la `Session` de Flet en memoria, sin Flutter ni display.
   - Permite navegar (`await app.goto("/ruta")`), buscar controles (`app.find(text=..., type=..., key=...)`), hacer clic (`await app.click(ctrl)`), escribir (`await app.fill(ctrl, "valor")`) y elegir opciones (`await app.select(dropdown, "valor")`).
   - Cualquier excepción en un handler queda en `app.errors`. Termina siempre con `app.assert_no_errors()`.
   - Para un servicio del cliente (FilePicker, etc.), registra la respuesta en `app.client_methods["pick_files"] = lambda args: [...]`.
   - Cada sesión de pytest usa una SQLite temporal. Las vistas que llaman a la API con `requests` se redirigen al `TestClient` de FastAPI.
2. **Revisión visual (`make screenshots`)**. Levanta la app en modo web y la API, abre cada ruta en Chromium headless y guarda PNGs en `screenshots/`. Lee las imágenes para comprobar cómo se ve.
   - `screenshots/report.json` marca las rutas en blanco, con redirecciones inesperadas o con errores de consola.
   - `screenshots/server.log` y `screenshots/api.log` guardan los tracebacks.
   - Los servidores usan una copia de `template.db`, así que no modifican datos.

Si agregas una vista nueva, regístrala en `src/controls/router/views.py` y añádela a `ROUTES` en `tests/test_routes.py`. Una prueba falla si falta. Agrega también una prueba de flujo en `tests/test_flows.py` si la vista tiene interacción.

## Flet 1.x: diferencias que importan (respecto a 0.28)

- **Entrada y navegación:**
  - `ft.run(main)` reemplaza a `ft.app(target=...)`.
  - `page.navigate(route)` (sync) o `await page.push_route(route)` reemplazan a `page.go(...)`.
- **Diálogos:**
  - `page.show_dialog(dlg)` abre un diálogo.
  - `page.pop_dialog()` cierra **el diálogo abierto más reciente**, que puede ser un SnackBar. Para cerrar uno concreto usa `controls.utils.close_dialog(dlg)`.
- **Helpers de estilo:** `ft.Padding.all/only/symmetric`, `ft.Margin.*`, `ft.Border.*`, `ft.BorderRadius.*`, `ft.Alignment.CENTER`, etc. Los módulos en minúscula (`ft.padding`, `ft.alignment`, …) ya no existen.
- **Alineación de `Row` y `Column`:** usa `ft.MainAxisAlignment` / `ft.CrossAxisAlignment`, nunca `ft.Alignment`. Flet no lo valida, pero `tests/test_routes.py::test_route_control_types` sí.
- **Botones:** `ft.Button(content=...)` reemplaza a `ElevatedButton(text=...)`. Todos los `text=` de los botones pasan a `content=`.
- **Constructores:** los controles son dataclasses y los kwargs desconocidos lanzan `TypeError`.
- **Dropdown:** `on_select` reemplaza a `on_change`, y las opciones son `ft.DropdownOption(key, text)`.
- **Charts:** viven en `flet_charts` (`import flet_charts as fch`).
- **`control.page`:** lanza `RuntimeError` si el control no está montado. No lo uses como booleano; usa `controls.utils.is_mounted(ctrl)` / `safe_update(ctrl)`. Las subclases de controles no deben asignar `self.page`; usa otro nombre, como `self.app_page`.
- **Servicios:**
  - `ft.FilePicker()`, `ft.UrlLauncher()`, etc. se registran solos en la página.
  - Sus métodos son `async`: `files = await picker.pick_files(...)`.
  - `TextField.focus()` también es async.
- **Tareas de fondo:** usa `page.run_task(coroutine_fn)` con `asyncio.sleep`. No uses hilos que llamen a `update()`.
- **Assets:**
  - Se referencian relativos a `src/assets` (`src="image/icon.png"`).
  - En web se sirven en la raíz: una ruta de la app no puede llamarse igual que una carpeta de `src/assets`. `test_routes_do_not_collide_with_assets` lo verifica.
  - Para SVG en memoria usa `ft.Image(src=svg_bytes)`.
- **Referencia:** el código fuente del SDK instalado está en `.venv/lib/python3.13/site-packages/flet/`. Ahí se puede revisar cualquier API.

## Estructura

- `src/main.py`: `AppTemplate` + `main(page)`.
- `src/settings.py`: rutas y configuración (`FLETBATTERIES_DB_URL`, `FLETBATTERIES_API_URL`, `FLETBATTERIES_SKIP_LOGIN`).
- `src/controls/router/`: vistas registradas (`views.py`) y router.
- `src/components/shared/`: componentes reutilizables (form, datatable, calendar, color_picker, selects, …).
- `src/data/models` y `src/data/manager`: modelos SQLAlchemy y managers CRUD. El modelo nuevo se registra en `src/scripts/init_db.py`.
- `src/scripts/api.py`: API FastAPI (`make api`).
- `tests/`: harness y pruebas.
- `tools/screenshots.py`: capturas.
