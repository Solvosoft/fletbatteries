"""
CRUD declarativo: tabla (o tarjetas) + modales de crear, editar, ver y eliminar.
Equivale a `CRUDView` / `ObjectManagement` de djgentelella.

    class CustomerCRUD(CRUDView):
        title = "Clientes"
        name = "cliente"
        manager = CustomerManager()        # o source = APISource(...) / model = Customer
        form_class = CustomerForm
        list_fields = ["name", "email", "phone"]
        filter_fields = ["name", "email"]
        permissions = {"delete": "customers.delete"}

    content = CustomerCRUD(page).build()

Hooks para personalizar: `get_initial(item)`, `prepare_data(data, item)`,
`after_save(item, created)`, `detail_controls(item)`, `get_extra_actions()`,
`get_bulk_actions()`.

Opciones extra (todas desactivadas por defecto):

- `actions = ACTIONS + ("clone",)`: botón "Duplicar" (abre "Agregar" con los datos).
- `bulk_delete = True` / `bulk_actions = [BulkAction(...)]`: selección y acciones masivas.
- `export = True` (`export_fields`): botón "Exportar CSV" con la búsqueda y filtros actuales.
- `importable = True` (`import_fields`, `import_key_field`): importar desde CSV.
- `undo_delete = True` (por defecto): si el manager usa `TrashMixin`, el aviso
  de "Eliminado" trae el botón "Deshacer".

Permisos opcionales en `permissions`: "clone" (si falta usa el de "create"),
"export" e "import".
"""

import logging
from typing import Any, Optional, Sequence

import flet as ft
from sqlalchemy.exc import IntegrityError

from fletbatteries.auth.session import get_user, has_perm
from fletbatteries.data.manager import BaseManager
from fletbatteries.data.source import DataSource, SQLAlchemySource
from fletbatteries.forms.validators import ValidationError
from fletbatteries.i18n import _, ngettext
from fletbatteries.utils import notify
from fletbatteries.widgets.cardlist import CardList, default_card
from fletbatteries.widgets.datatable import BulkAction, DataTable, RowAction, filter_form_for
from fletbatteries.widgets.modals import CrudModal

log = logging.getLogger(__name__)

ACTIONS = ("create", "edit", "delete", "detail")


class CRUDView:
    title: Optional[str] = None
    name: Optional[str] = None
    source: Optional[DataSource] = None
    manager: Optional[BaseManager] = None
    model: Any = None
    form_class: Any = None
    list_fields: Optional[Sequence] = None
    filter_fields: Optional[Sequence[str]] = None
    filter_form: Any = None
    actions: Sequence[str] = ACTIONS
    extra_actions: Sequence[RowAction] = ()
    permissions: dict = {}
    mode: str = "table"  # "table" | "cards"
    card: Any = None
    page_size: int = 10
    modal_width: int = 640
    order_by: Optional[str] = None
    fixed_filters: dict = {}
    selectable: bool = False
    bulk_delete: bool = False
    bulk_actions: Sequence[BulkAction] = ()
    export: bool = False
    export_fields: Optional[Sequence] = None
    importable: bool = False
    import_fields: Optional[Sequence[str]] = None
    import_key_field: Optional[str] = None
    undo_delete: bool = True

    # Registro en el app shell (ver fletbatteries.app)
    route: Optional[str] = None
    icon: Any = ft.Icons.TABLE_VIEW

    def __init__(self, page: ft.Page, **options):
        for key, value in options.items():
            if not hasattr(type(self), key):
                raise TypeError(f"{type(self).__name__} no tiene la opción '{key}'")
            setattr(self, key, value)
        self.page = page
        self.modal = CrudModal(page)
        self.list_widget: Optional[ft.Control] = None
        self.current_form = None
        self.source = self.get_source()

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------
    def get_source(self) -> DataSource:
        if self.source is not None:
            return self.source
        manager = self.manager
        if manager is None and self.model is not None:
            manager = BaseManager(self.model)
        if manager is None:
            raise ValueError(f"{type(self).__name__}: defina `source`, `manager` o `model`")
        return SQLAlchemySource(manager)

    def get_title(self) -> str:
        if self.title:
            return self.title
        return getattr(self.form_class, "title", None) or type(self).__name__

    def get_name(self) -> str:
        return self.name or self.get_title()

    def get_form(self, item: Optional[dict] = None):
        """Formulario para crear (`item=None`) o editar; los valores salen de `instance` y `get_initial`."""
        return self.form_class(initial=self.get_initial(item), instance=item)

    def get_initial(self, item: Optional[dict]) -> dict:
        """Valores iniciales extra (además de los del registro)."""
        return {}

    def get_filter_form(self):
        if self.filter_form is not None:
            return self.filter_form
        if self.filter_fields and self.form_class is not None:
            return filter_form_for(self.form_class, self.filter_fields)
        return None

    def can(self, action: str) -> bool:
        if action == "export":
            return self.export and has_perm(self.page, self.permissions.get("export"))
        if action == "import":
            return self.importable and self.form_class is not None and has_perm(self.page,
                                                                                 self.permissions.get("import"))
        if action not in self.actions:
            return False
        if action == "clone":
            return has_perm(self.page, self.permissions.get("clone", self.permissions.get("create")))
        return has_perm(self.page, self.permissions.get(action))

    def get_extra_actions(self) -> list[RowAction]:
        actions = list(self.extra_actions)
        if self.has_history() and has_perm(self.page, self.permissions.get("history")):
            actions.append(RowAction(ft.Icons.HISTORY, _("History"), self.open_history, name="history"))
        return actions

    def has_history(self) -> bool:
        return hasattr(getattr(self.source, "manager", None), "history")

    def row_actions(self) -> list[RowAction]:
        actions = []
        if self.can("detail"):
            actions.append(RowAction(ft.Icons.VISIBILITY_OUTLINED, _("Detail"), self.open_detail, name="detail"))
        if self.can("edit"):
            actions.append(RowAction(ft.Icons.EDIT_OUTLINED, _("Edit"), self.open_edit, name="edit"))
        if self.can("clone"):
            actions.append(RowAction(ft.Icons.CONTENT_COPY, _("Duplicate"), self.open_clone, name="clone"))
        if self.can("delete"):
            actions.append(RowAction(ft.Icons.DELETE_OUTLINE, _("Delete"), self.open_delete, name="delete",
                                     color=ft.Colors.ERROR))
        return actions + self.get_extra_actions()

    def top_actions(self) -> list[ft.Control]:
        controls = []
        if self.can("import"):
            controls.append(ft.IconButton(icon=ft.Icons.UPLOAD_FILE, tooltip=_("Import CSV"), key="crud_import",
                                          on_click=lambda e: self.open_import()))
        if self.can("create"):
            controls.append(ft.Button(content=_("Add"), icon=ft.Icons.ADD, key="crud_add",
                                      on_click=lambda e: self.open_create()))
        return controls

    def get_bulk_actions(self) -> list[BulkAction]:
        actions = list(self.bulk_actions)
        if self.bulk_delete and self.can("delete"):
            actions.append(BulkAction("delete", _("Delete selected"), self.delete_many, icon=ft.Icons.DELETE_OUTLINE,
                                      color=ft.Colors.ERROR,
                                      confirm_text=_("Are you sure you want to delete the selected records?")))
        return actions

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def build_list(self) -> ft.Control:
        if self.mode == "cards":
            card = self.card or default_card(
                [c if isinstance(c, str) else c.name for c in (self.list_fields or self.form_class.base_fields)],
                title_field=(self.list_fields or list(self.form_class.base_fields))[0],
                form=self.form_class,
            )
            return CardList(self.source, card=card, actions=self.row_actions(), top_actions=self.top_actions(),
                            page_size=self.page_size, filters=self.fixed_filters, order_by=self.order_by)
        return DataTable(
            self.source,
            columns=self.list_fields,
            form=self.form_class,
            actions=self.row_actions(),
            top_actions=self.top_actions(),
            filter_form=self.get_filter_form(),
            page_size=self.page_size,
            order_by=self.order_by,
            base_filters=self.fixed_filters,
            selectable=self.selectable,
            bulk_actions=self.get_bulk_actions(),
            exportable=self.can("export"),
            export_columns=self.export_fields,
            export_name=self.get_title(),
        )

    def build(self) -> ft.Control:
        self.list_widget = self.build_list()
        return ft.Container(
            expand=True,
            padding=10,
            content=ft.Column(
                [ft.Text(self.get_title(), size=20), ft.Divider(), self.list_widget],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def reload(self):
        if self.list_widget is not None:
            self.list_widget.reload()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def open_create(self):
        form = self.current_form = self.get_form()
        self.modal.open(
            kind="create",
            title=_("Add {name}", name=self.get_name()),
            content_controls=[form.control],
            on_accept=lambda: self.save(form, None),
            success_text=_("Saved successfully"),
            width=self.modal_width,
        )

    def open_edit(self, item: dict):
        fresh = self.source.get(item["id"]) or item
        form = self.current_form = self.get_form(fresh)
        self.modal.open(
            kind="edit",
            title=_("Edit {name}", name=self.get_name()),
            content_controls=[form.control],
            on_accept=lambda: self.save(form, fresh),
            success_text=_("Saved successfully"),
            width=self.modal_width,
        )

    def open_clone(self, item: dict):
        """Abre "Agregar" con los datos del registro (sin su id ni los campos únicos)."""
        fresh = self.source.get(item["id"]) or item
        data = dict(fresh)
        data.pop(getattr(self.source, "pk_field", "id"), None)
        data.pop("id", None)
        manager = getattr(self.source, "manager", None)
        for name in getattr(manager, "unique_fields", ()) or ():
            data.pop(name, None)
        form = self.current_form = self.form_class(initial={**data, **self.get_initial(None)})
        self.modal.open(
            kind="create",
            title=_("Duplicate {name}", name=self.get_name()),
            content_controls=[form.control],
            on_accept=lambda: self.save(form, None),
            success_text=_("Saved successfully"),
            width=self.modal_width,
        )

    def open_delete(self, item: dict):
        self.modal.open(
            kind="delete",
            title=_("Delete {name}", name=self.get_name()),
            content_controls=[ft.Text(_("Are you sure you want to delete this record?")),
                              ft.Text(self.source.to_label(item), weight=ft.FontWeight.BOLD)],
            on_accept=lambda: self.delete(item),
            success_text=_("Deleted successfully"),
            success_action=self.undo_action(item),
            width=self.modal_width,
        )

    def can_restore(self) -> bool:
        return self.undo_delete and hasattr(getattr(self.source, "manager", None), "restore")

    def undo_action(self, item: dict) -> Optional[tuple]:
        """Botón "Deshacer" del aviso de eliminado (solo si el manager tiene papelera)."""
        if not self.can_restore():
            return None
        return _("Undo"), lambda: self.restore(item)

    def restore(self, item: dict) -> bool:
        try:
            with self.acting_user():
                ok = self.source.manager.restore(item["id"])
        except Exception:
            log.exception("Error restaurando %s", self.get_name())
            ok = False
        self.reload()
        notify(self.page, _("Restored successfully") if ok else _("Sorry, an error occurred"), success=ok)
        return ok

    def open_import(self):
        from fletbatteries.crud.import_dialog import ImportDialog
        from fletbatteries.data.importer import CSVImporter

        importer = CSVImporter(self.form_class, self.source, key_field=self.import_key_field,
                               fields=self.import_fields, fixed_data=self.fixed_filters)
        dialog = ImportDialog(self.page, importer, title=f"{_('Import CSV')}: {self.get_title()}",
                              on_done=lambda counts: self.reload(), wrap=self.acting_user)
        dialog.open()
        return dialog

    def open_detail(self, item: dict):
        fresh = self.source.get(item["id"]) or item
        self.modal.open(
            kind="detail",
            title=_("Detail of {name}", name=self.get_name()),
            content_controls=self.detail_controls(fresh),
            width=self.modal_width,
        )

    def open_history(self, item: dict):
        from fletbatteries.contrib.history import history_controls

        self.modal.open(
            kind="detail",
            title=f"{_('History')}: {self.source.to_label(item)}",
            content_controls=history_controls(self.source.manager.history(item["id"])),
            width=self.modal_width,
        )

    def detail_controls(self, item: dict) -> list[ft.Control]:
        rows = []
        fields = self.form_class.base_fields if self.form_class else {}
        for name, field in fields.items():
            rows.append(
                ft.Row(
                    [
                        ft.Text(field.label or name, weight=ft.FontWeight.BOLD, width=180),
                        ft.Text(field.display(item.get(name)), expand=True, selectable=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            )
        return rows

    def acting_user(self):
        """Usuario de la sesión para el historial y la papelera."""
        from fletbatteries.contrib.history import acting_as

        return acting_as(get_user(self.page))

    def prepare_data(self, data: dict, item: Optional[dict]) -> dict:
        return data

    def after_save(self, item: dict, created: bool):
        pass

    def save(self, form, item: Optional[dict]) -> Optional[bool]:
        if not form.is_valid():
            return None
        try:
            data = self.prepare_data(form.save_data(), item)
            with self.acting_user():
                if item is None:
                    saved = self.source.create({**data, **self.fixed_filters})
                else:
                    saved = self.source.update(item["id"], data)
        except ValidationError as e:
            if e.error_dict:
                for name, messages in e.error_dict.items():
                    form.add_error(name if name in form.fields else None, messages)
            else:
                form.add_error(None, e)
            form.show_errors()
            return None
        except Exception as e:
            log.exception("Error guardando %s", self.get_name())
            form.add_error(None, str(e) or _("Sorry, an error occurred"))
            form.show_errors()
            return None
        self.after_save(saved, item is None)
        self.reload()
        return True

    def delete_error_message(self, error: Exception) -> str:
        if isinstance(error, IntegrityError):
            return _("This record is in use by other records and cannot be deleted.")
        if isinstance(error, (ValidationError, PermissionError)):
            return str(error)
        return _("The record could not be deleted: {error}", error=str(error) or type(error).__name__)

    def delete(self, item: dict):
        """`True` si se eliminó; si no, el mensaje de error que verá el usuario."""
        try:
            with self.acting_user():
                ok = self.source.delete(item["id"])
        except Exception as e:
            log.exception("Error eliminando %s", self.get_name())
            return self.delete_error_message(e)
        self.reload()
        return True if ok else _("The record no longer exists.")

    def delete_many(self, ids: list) -> str:
        """Acción masiva "Eliminar seleccionados"; devuelve el resumen para mostrar."""
        with self.acting_user():
            result = self.source.delete_many(ids)
        message = ngettext("{n} record deleted.", "{n} records deleted.", result.count)
        if result.failed:
            message += " " + ngettext("{n} record could not be deleted.", "{n} records could not be deleted.",
                                      len(result.failed))
        return message

    # ------------------------------------------------------------------
    # Atajo para registrar en el router
    # ------------------------------------------------------------------
    @classmethod
    def as_view(cls, **options):
        """Devuelve `builder(page) -> Control` para usar en el registro de vistas."""
        return lambda page: cls(page, **options).build()


class InlineCRUD(CRUDView):
    """CRUD de registros hijos de un padre (p. ej. las direcciones de un cliente)."""

    parent_field: Optional[str] = None
    parent_id: Any = None

    def __init__(self, page: ft.Page, parent_id=None, **options):
        super().__init__(page, **options)
        if parent_id is not None:
            self.parent_id = parent_id
        if not self.parent_field:
            raise ValueError(f"{type(self).__name__}: defina `parent_field`")
        self.fixed_filters = {**self.fixed_filters, self.parent_field: self.parent_id}

    def get_form(self, item: Optional[dict] = None):
        form = super().get_form(item)
        if self.parent_field in form.fields:
            form.fields[self.parent_field].disabled = True
            form.initial.setdefault(self.parent_field, self.parent_id)
        return form

    def build(self) -> ft.Control:
        self.list_widget = self.build_list()
        return ft.Container(content=self.list_widget, expand=True)
