# Guía para agentes

FletBatteries es un framework para Flet **1.0.4** inspirado en django-gentelella-widgets (Python 3.13, entorno gestionado con `uv`). Tiene dos partes:

- `src/fletbatteries/`: el paquete instalable (formularios declarativos, widgets, CRUD, app shell, contrib). Se importa como `from fletbatteries...`.
- `demo/`: la app de ejemplo que usa el paquete. Se ejecuta con `demo/` en el `PYTHONPATH`, por eso sus imports son `from views...`, `from data...`, etc.

Lo genérico va en `src/fletbatteries/` (con textos en inglés envueltos en `_()` y su traducción en `src/fletbatteries/i18n/es.py`); lo específico de la demo va en `demo/`.

## Comandos

```bash
make setup                 # primera vez: recrea .venv, instala dependencias y crea las tablas
make sync                  # actualizar .venv después de cambiar pyproject.toml / uv.lock
make test                  # pruebas headless (siempre antes de terminar un cambio)
make test PYTEST_ARGS="-k calendar -x"
make screenshots ROUTES="/calendar"   # revisión visual: screenshots/calendar.png
make lint
make makemigrations MSG="agregar campo"   # nueva migración (Alembic) a partir de los modelos
make migrate                              # aplicar migraciones
```

Para agregar una dependencia usa `uv add <paquete>` (o `uv add --dev <paquete>`) y luego `make requirements`.

## Cómo verificar un cambio

1. **Pruebas automáticas (`make test`)**. Son deterministas y no dependen de un agente: si pasan, el cambio funciona.
   - `tests/harness.py` (`AppHarness`) ejecuta el `main(page)` real contra la `Session` de Flet en memoria, sin Flutter ni display.
   - Permite navegar (`await app.goto("/ruta")`), buscar controles (`app.find(text=..., type=..., key=...)`), hacer clic (`await app.click(ctrl)`), escribir (`await app.fill(ctrl, "valor")`) y elegir opciones (`await app.select(dropdown, "valor")`).
   - Cualquier excepción en un handler queda en `app.errors`. Termina siempre con `app.assert_no_errors()`.
   - En cada `settle()` el harness revisa el layout con `layout_errors()` (por ejemplo un hijo con `expand` dentro de un `ListView` o de un `Row(wrap=True)`, que Flutter dibuja como una caja gris) y lo agrega a `app.errors`. Así se validan también los estados intermedios: dropdowns abiertos, diálogos, etc.
   - Para un servicio del cliente (FilePicker, etc.), registra la respuesta en `app.client_methods["pick_files"] = lambda args: [...]`.
   - Cada sesión de pytest usa una SQLite temporal. Las vistas que llaman a la API con `requests` se redirigen al `TestClient` de FastAPI.
2. **Revisión visual (`make screenshots`)**. Levanta la app en modo web y la API, abre cada ruta en Chromium headless y guarda PNGs en `screenshots/`. Lee las imágenes para comprobar cómo se ve.
   - `screenshots/report.json` marca las rutas en blanco, con redirecciones inesperadas o con errores de consola.
   - `screenshots/server.log` y `screenshots/api.log` guardan los tracebacks.
   - Los servidores usan una copia de `template.db`, así que no modifican datos.
   - Para revisar estados interactivos, las vistas aceptan un query: `make screenshots ROUTES="/widgets?visual=open /modals?visual=form"` abre los dropdowns, pone el Markdown en vista previa y carga una imagen ya guardada (dentro de un modal en el segundo caso). Usa `fletbatteries.utils.route_query(page)` y `run_after_mount(page, fn)` para agregar estados así en otras vistas.
3. **Escritorio (`make run`)**. En Linux, Flet usa el cliente "light", que no incluye extensiones como Rive o mapas ("Unknown control: Rive"). `make run FLAVOR=full` usa el cliente full (requiere `libmpv2`), pero en Debian 13 se cierra al arrancar: la `libstdc++` que carga libmpv reemplaza el `operator new` de la libc++ de Flutter. Para tener Rive, charts y mapas en escritorio: `make build-linux` (requiere `clang`; la primera vez descarga Flutter) compila la app solo con las extensiones de `[tool.flet.linux]` en `pyproject.toml`, sin libmpv, y `make run-build` la ejecuta con el `template.db` del repo y `GDK_GL=gles` (con GLX, `rive_native` avisa "EGLImage unavailable" y no dibuja o rompe el contexto GL). Para depurar la app compilada: `FLETBATTERIES_INITIAL_ROUTE=/ruta` abre directo en esa vista y `FLETBATTERIES_LOG_FILE=/tmp/app.log` guarda el log de Python.

Si agregas una vista nueva, regístrala en `demo/controls/router/views.py` y añádela a `ROUTES` en `tests/test_routes.py`. Una prueba falla si falta. Agrega también una prueba de flujo en `tests/test_flows.py` si la vista tiene interacción.

**La librería no depende de la demo.** Lo genérico se configura con parámetros, settings o variables `FLETBATTERIES_*` que lee la propia librería; las vistas del framework se registran con helpers (`app.add_admin_views()`, `app.add_account_views()`). `tests_lib/` prueba la librería con sus propios modelos (`tests_lib/models.py`, otra `Base`) y una app mínima, sin importar `demo/`; `tests_lib/test_independence.py` falla si `src/` importa módulos de la demo.

Si cambias un modelo (de la demo o del framework), genera la migración con `make makemigrations MSG="..."` (las revisiones de la demo están en `demo/migrations/`) y aplica `make migrate` también sobre `template.db`. `tests/test_migrations.py` verifica que las migraciones y `template.db` coincidan con los modelos.

## Flet 1.x: diferencias que importan (respecto a 0.28)

- **Entrada y navegación:**
  - `ft.run(main)` reemplaza a `ft.app(target=...)`.
  - `page.navigate(route)` (sync) o `await page.push_route(route)` reemplazan a `page.go(...)`.
- **Diálogos:**
  - `page.show_dialog(dlg)` abre un diálogo.
  - `page.pop_dialog()` cierra **el diálogo abierto más reciente**, que puede ser un SnackBar. Para cerrar uno concreto usa `fletbatteries.utils.close_dialog(dlg)`.
- **Helpers de estilo:** `ft.Padding.all/only/symmetric`, `ft.Margin.*`, `ft.Border.*`, `ft.BorderRadius.*`, `ft.Alignment.CENTER`, etc. Los módulos en minúscula (`ft.padding`, `ft.alignment`, …) ya no existen.
- **Alineación de `Row` y `Column`:** usa `ft.MainAxisAlignment` / `ft.CrossAxisAlignment`, nunca `ft.Alignment`. Flet no lo valida, pero `tests/test_routes.py::test_route_control_types` sí.
- **Botones:** `ft.Button(content=...)` reemplaza a `ElevatedButton(text=...)`. Todos los `text=` de los botones pasan a `content=`.
- **Constructores:** los controles son dataclasses y los kwargs desconocidos lanzan `TypeError`.
- **Dropdown:** `on_select` reemplaza a `on_change`, y las opciones son `ft.DropdownOption(key, text)`.
- **Charts:** viven en `flet_charts` (`import flet_charts as fch`).
- **`control.page`:** lanza `RuntimeError` si el control no está montado. No lo uses como booleano; usa `fletbatteries.utils.is_mounted(ctrl)` / `safe_update(ctrl)` / `get_page(ctrl)`. Las subclases de controles no deben asignar `self.page`; usa otro nombre, como `self.app_page`.
- **Archivos ya guardados:** al editar, `FileField`/`ImageField` convierten el nombre guardado en `UploadedFile(stored=True)` (con `media_url` para la vista previa). `save_file` solo copia los archivos nuevos (`is_new`).
- **Subclases de controles:** no definas atributos privados que Flet ya usa (por ejemplo `_notify`, que el SDK llama en cada cambio de propiedad). Un `Row(wrap=True)` no admite hijos con `expand` (Flutter dibuja una caja gris); `test_route_control_types` lo detecta.
- **Servicios:**
  - `ft.FilePicker()`, `ft.UrlLauncher()`, etc. se registran solos en la página.
  - Sus métodos son `async`: `files = await picker.pick_files(...)`.
  - `TextField.focus()` también es async.
- **Tareas de fondo:** usa `page.run_task(coroutine_fn)` con `asyncio.sleep`. No uses hilos que llamen a `update()`.
- **Assets:**
  - Se referencian relativos a `demo/assets` (`src="image/icon.png"`).
  - En web se sirven en la raíz: una ruta de la app no puede llamarse igual que una carpeta de `demo/assets`. `test_routes_do_not_collide_with_assets` lo verifica.
  - Para SVG en memoria usa `ft.Image(src=svg_bytes)`.
- **Referencia:** el código fuente del SDK instalado está en `.venv/lib/python3.13/site-packages/flet/`. Ahí se puede revisar cualquier API.

## Estructura

### Paquete `src/fletbatteries/`

- `app.py`: `FletBatteriesApp` (registro de vistas con `add_view` / `@app.view` / `add_crud`, rutas con parámetros `/x/:id`, guards de login y permisos, menú con badges y ítems de footer, breadcrumbs, tema persistente, selector de idioma, `password_validators`, `session_idle_minutes`/`session_max_minutes`, `add_account_views()` y `add_admin_views()`) y `AppShell` (estado por sesión, `shell_of(page)`).
- `cli.py` / `data/migrations.py` / `migrations/`: CLI `fletbatteries` (`makemigrations`, `migrate`, `check`, `createdb`, `createsuperuser`…) con un `env.py` de Alembic genérico; se configura con `[tool.fletbatteries]` en `pyproject.toml` o variables `FLETBATTERIES_*`.
- `forms/`: `Form` y `ModelForm` declarativos (render `plain`/`horizontal`/`inline`/`grid`; `fieldsets` como `sections`/`tabs`/`collapsible`; FK y M2M a selects de registros), `fields.py` (CharField, DateField, ChoiceField, ModelChoiceField, FileField, MarkdownField, MapPointField, …; `from_text()` para importar), validadores, `formset_factory`, `FormWizard` (pasos con condiciones), `validate_data()` (validar sin widgets). Campos dependientes con `depends_on` + `related_choices`/`related_filter`.
- `widgets/`: controles con el contrato `value` / `error` / `on_change` (`base.Widget`): inputs, máscaras, fechas (formato según el idioma), selects con búsqueda (`selects.py`), choices avanzados, sliders, archivos, color, Markdown, mapas, `DataTable` server-side (búsqueda con debounce, `BulkAction`, selección entre páginas, exportar CSV), `CardList`, `CrudModal`, calendario, gráficos y stat tiles.
- `data/`: `Database`/`set_default_database`/`import_models`, `BaseManager` (CRUD, filtros `campo__op` con `gt`/`lt`/`ne`/`startswith`/…, relaciones `rel__campo`, `__or__`, búsqueda, orden, paginación, `unique_fields` con error por campo, `delete_many`/`update_many`), `DataSource` (`SQLAlchemySource`, `APISource` con `token`, `ListSource`), `export.py` (CSV) e `importer.py` (`CSVImporter` con vista previa).
- `crud/`: `CRUDView` (opcionales: `clone`, `bulk_delete`/`bulk_actions`, `export`, `importable`, deshacer al borrar con papelera), `InlineCRUD` e `ImportDialog`.
- `api/`: `crud_router(manager, prefix=..., auth=True, perms="app")` para FastAPI (lo consume `APISource`), `auth_router()` (tokens) y las dependencias `current_api_user` / `require_perms`.
- `auth/`: sesión (`login`, `get_user`, `has_perm`), modelos `fb_users`/`fb_groups`/`fb_permissions`/`fb_login_attempts`/`fb_password_resets`/`fb_api_tokens`, `DatabaseAuthBackend` (bloqueo por intentos, `AuthError`), `password_validation`, `reset.py` (código por correo), `tokens.py`, vistas de login, cuenta (cambiar/recuperar contraseña, tokens) y CRUD de administración (incluido el registro de ingresos).
- `layout/`: navbar, sidebar, breadcrumbs, footer, `MenuItem`.
- `contrib/`: `settings` (configuración en BD y `SettingCRUD` en `/admin/settings`), `notifications` (campana), `help` (ayuda editable), `history` (`HistoryMixin`, `HistoryCRUD`), `trash` (`SoftDeleteMixin`, `TrashMixin`, `build_trash_view`), `email` (`send_mail`, backends SMTP/consola/memoria, `FLETBATTERIES_EMAIL_BACKEND`).
- `i18n/`: `_()`, `ngettext()`, `set_language(lang, page)` (por sesión), `set_default_language()`, `get_format("date")`; catálogo español en `es.py`. Los textos evaluados al definir una clase (`title = _("...")`) usan el idioma por defecto.

### Demo `demo/`

- `demo/main.py`: crea `app = FletBatteriesApp(...)` y `main(page)`.
- `demo/controls/router/views.py`: `register_views(app)`. Toda vista nueva se registra aquí y se agrega a `ROUTES` en `tests/test_routes.py` (una prueba falla si falta).
- `demo/settings.py`: configuración (`FLETBATTERIES_DB_URL`, `FLETBATTERIES_API_URL`, `FLETBATTERIES_SKIP_LOGIN`) y base de datos por defecto.
- `demo/app_forms.py`: formularios de la demo.
- `demo/data/models` y `demo/data/manager`: modelos y managers (`BaseManager`). Un modelo nuevo se importa en `demo/data/models/__init__.py` y en `demo/scripts/init_db.py`.
- `demo/scripts/api.py`: API FastAPI (`make api`). `init_db.py create_db` crea el usuario `admin`/`admin` (solo desarrollo).
- `tests/`: harness y pruebas de la demo. `logged_app` deja un superusuario en la sesión.
- `tests_lib/`: pruebas de la librería sin la demo (fixtures `db`, `admin`, `outbox`, `lib_app`).
- `demo/migrations/`: revisiones de Alembic de la demo (`[tool.fletbatteries]` en `pyproject.toml`).
- `tools/screenshots.py`: capturas.

### Ejemplo mínimo

```python
from fletbatteries import forms
from fletbatteries.app import FletBatteriesApp
from fletbatteries.crud import CRUDView

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "email"]

class CustomerCRUD(CRUDView):
    title = "Clientes"
    manager = CustomerManager()
    form_class = CustomerForm
    filter_fields = ["name"]

app = FletBatteriesApp(title="Mi app")
app.add_crud(CustomerCRUD, "/customers", icon=ft.Icons.PEOPLE)
app.run()
```
