# Hoja de ruta: funcionalidades faltantes en FletBatteries

## Contexto
FletBatteries (~10.6k LOC en `src/fletbatteries/`) ya cubre la base de un framework de administración: formularios declarativos con 30 tipos de campo, widgets estilo djgentelella, un `DataTable` paginado en el servidor, `CRUDView`/`InlineCRUD`, autenticación con permisos por acción, y los módulos contrib `settings`, `notifications`, `help`, `history` y `trash`, además de calendario, gráficos y mapas.

Se comparó con django-gentelella-widgets (DGW), Django admin y sus paquetes, Filament, React-Admin, Refine, Reflex, NiceGUI, flet-easy, Odoo y Retool/Appsmith. El objetivo es medir cuánto cuesta cerrar cada brecha y ordenarlas. En la investigación no apareció ningún framework de administración/CRUD para Flet, así que FletBatteries llena un hueco real. La búsqueda fue limitada: no se revisaron PyPI ni GitHub directamente.

**Escala de esfuerzo:** S = 1 día o menos · M = 2–4 días · L = 1–2 semanas · XL = más de 2 semanas. Incluye las pruebas en `tests/` y la vista en la demo.


---

## Estado (2026-10-14)
**Hechas la deuda técnica, la Fase 0 y la Fase 1.** Sus funciones, con el módulo donde viven:

- **Deuda técnica (sección 1, completa):**
  - Calendario traducido y con colores del tema; colores del tema en modo oscuro.
  - Búsqueda de la tabla con debounce; errores al borrar.
  - Únicos con el error en el campo; lookups nuevos y `__or__`.
  - FK/M2M en `ModelForm`; validadores nuevos.
  - Idioma por sesión, fechas según el idioma, ítems de menú en el footer.
- **Fase 0:**
  - Deshacer al borrar (`undo_delete`) y duplicar (`clone`).
  - Cambio de contraseña (`/account/password`).
  - UI de configuración (`/admin/settings`).
  - Badges en el menú (`Route.badge`).
- **Fase 1:**
  - Tablas: acciones masivas (`BulkAction`, `bulk_delete`); exportar e importar CSV (`data/export.py`, `data/importer.py`, `ImportDialog`).
  - Formularios: fieldsets como pestañas, secciones o colapsables, y `FormWizard`.
  - Base de datos: migraciones con Alembic (CLI `fletbatteries`).
  - Seguridad: bloqueo por intentos y registro de ingresos (`/admin/logins`); expiración de sesión.
  - API: tokens (`auth_router`, `crud_router(auth=True)`, `/account/tokens`).
  - Correo: `contrib/email.py`, y recuperación de contraseña con un código (`/password-reset`).
- **Pendiente:** XLSX/PDF. Se decidió que la exportación y la importación sean solo CSV.

## 1. Deuda y pulido de lo existente (prioridad alta, costo bajo)
| Ítem | Detalle | Esfuerzo |
|---|---|---|
| Calendario sin i18n | Textos en español fijos ("Nuevo evento", "Guardar"…), nombres mezclados (`verifyForm`, `NombreEvento`) y colores fijos. Hay que pasar los textos por `_()` en `widgets/calendar.py` | S |
| Colores fijos en modo oscuro | Unos 29 usos de `Colors.BLACK`/`white`/`red` (`utils.show_snackbar`, `text_with_truncate`, calendario). Hay que usar los colores del tema | S |
| Búsqueda del DataTable sin debounce | Hoy consulta en cada tecla. Se puede reutilizar el debounce de `widgets/selects.py` | S |
| Errores al borrar | `CRUDView` devuelve `False` sin avisar. Falta mostrar el error con `show_snackbar` | S |
| `validate_unique` | Lanza `ValueError`; debería lanzar `ValidationError` para que el error aparezca en el campo | S |
| Lookups del manager | Faltan `gt`, `lt`, `ne`, `startswith`, `rel__field` y consultas OR (en `data/manager.py`) | M |
| `ModelForm` | No mapea FK/M2M a `ModelChoiceField`/`ModelMultipleChoiceField`, ni columnas UUID/JSON | M |
| Validadores | Faltan tamaño de archivo, dimensiones de imagen, slug, IP, teléfono y fortaleza de contraseña | S |
| Idioma por sesión | `set_language` es global del proceso; debería guardarse en `AppShell`. Faltan plurales y un catálogo `en` explícito | M |
| Fechas según locale | `%d/%m/%Y` está fijo en `widgets/dates.py` | S |
| `MenuItem.position="footer"` | La opción existe pero no se dibuja | S |

## 2. Tablas y listas
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| **Acciones masivas** (barra para borrar o ejecutar acciones sobre la selección) y selección que se mantiene al cambiar de página | DJA, FIL, RA, RF, OD | M |
| **Exportar CSV/XLSX** de la consulta filtrada (`openpyxl` como extra opcional) | IE, FIL, RA, RF, OD | M |
| **Importar CSV/XLSX** con vista previa, simulación y errores por fila | IE, FIL, RA-EE, OD | L |
| Columnas configurables (mostrar/ocultar) y orden por varias columnas | RA, FIL, OD | M |
| Edición en línea de celdas | DJA, FIL, RA-EE, RF | L |
| Filtros guardados y estado de la tabla en la URL (`route_query`) | RA, OD | M |
| Filas expandibles, totales y agrupación | FIL, OD | M–L |
| Vista **Kanban** por estado, con arrastrar y soltar | OD, FIL (plugin) | L |
| Vista de árbol (listas jerárquicas) | RA-EE, OD | M |
| Pivot / cohortes | OD, RA-EE | XL |
| Gantt / planificador | OD, RA-EE | XL |

## 3. CRUD y administración
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| Duplicar registro | FIL, RA, OD | S |
| Páginas completas de crear/editar/ver (`/x/:id/edit`), además de los modales | FIL, RA, DJA | M |
| Permisos por objeto o por fila (reglas sobre `base_query` y `has_object_perm`) | GU, OD, FIL | L |
| Permisos por campo (ocultar o bloquear campos según el rol) | RA-EE, OD | M |
| Revisiones con diff y "revertir" (`contrib.history` ya guarda el diff) | RV, SH, RA-EE | M |
| Deshacer al borrar (snackbar "Deshacer" usando `trash`) | RA, RF | S |
| Bloqueo optimista (`version_id`) para ediciones concurrentes | RA-EE | M |
| UI de configuración (editar `contrib.settings`) | DGW, OD | S |
| Comentarios / chatter en un registro | OD | M |
| Multi-tenant (filtro por tenant en manager, history y trash) | FIL, OD, DGW | XL |
| Menú editable en BD y gestión visual de permisos por categoría | DGW | M |

## 4. Formularios y widgets
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| **Fieldsets, pestañas y secciones colapsables** en `Form` (`Meta.fieldsets`) | DJA, FIL, RA, OD | M |
| **Wizard / formulario por pasos** | FIL, RA-EE, RF, NG, OD | M |
| Visibilidad condicional declarativa (`visible_if`), generalizando `YesNoInput.bind_controls` | FIL, RA, OD | M |
| Aviso de cambios sin guardar | RA, FIL, OD | S |
| Modo solo lectura del formulario (para el detalle) | FIL (infolists), RA | S |
| Formsets ligados a modelos y reordenables | DJA, DGW | M |
| Editor de texto enriquecido (WYSIWYG), con webview y TinyMCE o un editor Flutter | DGW, FIL, RA, NG | L |
| Subida múltiple, zona de arrastre, límite de tamaño, recorte | DGW (chunked), FIL | M–L |
| Subida por partes en web (chunked) | DGW | L |
| Firma manuscrita (canvas) | OD, DGW (Firmador) | M |
| QR y código de barras: mostrar y escanear | — | S–M |
| Calificación con estrellas, editor clave-valor, editor de código | NG, FIL, OD | S c/u |
| Visor de PDF | DGW, OD | M (webview) |
| Captura de cámara, audio y video (flet-audio-recorder) | DGW, GR | M |
| Dictado por voz | DGW | L |
| Mapa: polígonos y líneas, clustering, mapa de calor (DJMap) | DGW, NG | M |
| Calendario: vistas de mes y día, eventos recurrentes, arrastrar para mover | DGW (FullCalendar), OD | L |
| Timeline / StoryMap | DGW | M |

## 5. Autenticación y seguridad
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| **Cambio de contraseña propio** y política de contraseñas | todos | S |
| **Bloqueo por intentos fallidos y expiración de sesión** | FIL, OD | M |
| Recuperar contraseña por email (requiere el módulo de email) | DJA, FIL, RA, OD | M |
| 2FA TOTP (`pyotp`, `qrcode`) | FIL, OD | M |
| OAuth/OIDC/LDAP como backends enchufables (`DatabaseAuthBackend` ya define el contrato) | RA, RF, ST, OD | L |
| Auth del API (`crud_router`): tokens/JWT y permisos por endpoint | FE (JWT), RF | M |
| Registro de logins y accesos | OD | S |
| Campos cifrados (AES) | DGW | M |
| Refrescar permisos durante la sesión (hoy se capturan solo al hacer login) | — | S |

## 6. Datos e infraestructura
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| **Migraciones con Alembic** (comandos en el Makefile y un `env.py` que use el `Base`) | DJA, RX, FIL | M |
| Operaciones masivas en el manager (bulk create/update/delete) y API de agregaciones | DJA, OD | M |
| `APISource`: reintentos, refresh de token, versión async | RA, RF | M |
| `crud_router`: PK no entera, subida de archivos, endpoints masivos, modelos de respuesta | — | M |
| Fixtures (cargar y volcar datos) | DJA, OD | S |
| Almacenamiento de archivos enchufable (local/S3) y miniaturas | DJA, FIL | M |
| Búsqueda global entre recursos y paleta de comandos (Ctrl+K) | FIL, UF, OD | M |

## 7. Tiempo real, notificaciones y trabajos en segundo plano
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| Notificaciones push entre sesiones con pub/sub en memoria (`page.pubsub` de Flet), sin polling | DGW (Channels), FIL, RA-EE | M |
| Listas que se refrescan solas cuando otro usuario cambia datos | RA-EE, RF, OD | M |
| Badges en el menú (contadores) | UF, FIL, OD | S |
| **Módulo de email** (plantillas, SMTP, envío async) | DGW, FIL, OD | M |
| Newsletters (lotes, reintentos, supresión, baja con un clic) | DGW | XL |
| Trabajos en segundo plano y cron (APScheduler como extra) | DGW (Celery), OD, NG | M |
| Reglas de automatización y aprobaciones / máquina de estados | OD, RT | L–XL |

## 8. Reportes y dashboards
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| Más gráficos: área, radar, gauge, y exportar el gráfico a imagen | DGW, FIL | M |
| Dashboard declarativo (widgets en grilla, por permiso) | FIL, UF | M |
| Dashboard personalizable por el usuario (arrastrar, layout persistido) | RT, AS, OD | L |
| Reportes PDF / impresión (plantillas a PDF) | OD, RT | L |

## 9. UI, accesibilidad y responsive
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| **Layout responsive**: breakpoints con `on_resize`, drawer en móvil, `DataTable` que pasa a `CardList` | todos | L |
| Accesibilidad: `Semantics` y navegación por teclado | RA, DJA, FL | M |
| Selector de idioma en el navbar | RA, OD | S |
| Tema por usuario, presets de color y etiqueta de entorno (dev/prod) | JZ, UF | S |
| Tours guiados / onboarding | RA-EE | M |
| Atajos de teclado | OD | S |

## 10. Herramientas para desarrolladores
| Funcionalidad | Quién lo tiene | Esfuerzo |
|---|---|---|
| **CLI** `fletbatteries startproject` / `startapp` / `generate crud <Modelo>` (genera modelo, manager, form, CRUD, ruta y prueba) | DJA, FIL, RF, RX, FE, OD | L |
| Inferir el CRUD desde el modelo (`CRUDView(model=X)` sin form ni columnas) | RA, RF, FIL | M |
| Sistema de plugins (`app.install(plugin)` que registra vistas, menú, modelos y traducciones; los módulos contrib pasan a usarlo) | FIL, DJA, OD | M |
| Middleware y hooks de navegación (antes/después de la ruta, página de error de ruta) | FE, NG | S–M |
| **Sitio de documentación** (mkdocs con referencia de API, tutorial y galería de widgets con screenshots) | todos | L |
| Publicar `AppHarness` como `fletbatteries.testing` | FIL, NG | S |
| Ampliar ruff (I, B, UP) y agregar typing (pyright) | — | S–M |
| Publicar en PyPI y CI (GitHub Actions) | — | S |

---

## Hoja de ruta propuesta
1. **Fase 0: pulido** (sección 1, más deshacer, duplicar, cambio de contraseña, UI de settings y badges). Unas 2 semanas.
2. **Fase 1: administración "power".** Acciones masivas, exportar e importar, fieldsets/pestañas/wizard, Alembic, bloqueo por intentos y expiración de sesión, auth del API, módulo de email y recuperación de contraseña. 4–6 semanas.
3. **Fase 2: plataforma.** Plugins y middleware, CLI y generación de código, documentación, PyPI y CI, layout responsive, notificaciones en tiempo real, trabajos en segundo plano. 5–7 semanas.
4. **Fase 3: vistas avanzadas.** Kanban, árbol, edición en línea, permisos por objeto, WYSIWYG, calendario completo, reportes PDF, dashboards. 6–8 semanas.
5. **Fase 4: opcional / grande.** Multi-tenant, pivot, Gantt, newsletters, automatización y aprobaciones, voz y firma digital.

## Verificación
- Este documento: comprobar que cada brecha marcada como "ausente" lo está de verdad. Lo confirmó el inventario del código, por ejemplo: no hay `openpyxl` ni `alembic` en `pyproject.toml` y no hay UI de acciones masivas en `widgets/datatable.py`.
- Para cada funcionalidad que se implemente después: el flujo de `AGENTS.md`. Esto es `make test` con pruebas nuevas en `tests/test_flows.py` y `tests/test_crud.py`, la vista registrada en `demo/controls/router/views.py` y en `ROUTES`, y `make screenshots ROUTES="/ruta"` como revisión visual.
