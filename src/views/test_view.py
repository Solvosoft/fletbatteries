import flet as ft
from components.shared.modals import CrudModal
from controls.utils import get_form, show_snackbar
from components.shared.formset import Formset
import traceback

class TestView:
    def __init__(self, page: ft.Page, forms: []):
        self.page = page
        self.formset = None
        self.form = get_form(forms, "TestForm")
        self.data = [
            {"date": "01-01-2023", "datetime": "01-01-2023 12:00:00", "name": "Test 1"},
            {"date": "02-01-2023", "datetime": "02-01-2023 12:00:00", "name": "Test 2"},
            {"date": "03-01-2023", "datetime": "03-01-2023 12:00:00", "name": "Test 3"},
            {"date": "04-01-2023", "datetime": "04-01-2023 12:00:00", "name": "Test 4"},
            {"date": "05-01-2023", "datetime": "05-01-2023 12:00:00", "name": "Test 5"},
            {"date": "06-01-2023", "datetime": "06-01-2023 12:00:00", "name": "Test 6"},
        ]
        self.actions = [
            lambda form: ft.ElevatedButton(
                content=ft.Icon(ft.Icons.SAVE),
                on_click=lambda e, ft=form: self.handle_submit_click(ft)
            )
        ]
        self.delete_button = lambda form: ft.IconButton(
            icon=ft.Icons.CLOSE,
            tooltip="Delete this item",
            on_click=lambda e, ft=form: self.handle_delete_click(ft),
        )
        self.modal = CrudModal(self.page)

    def handle_submit_click(self, form):
        try:
            if form.is_valid():
                print("Form is valid")
                item = form.get_item()
                if item["id"] == 0 or item["id"] is None:
                    self.data.append(item)
                else:
                    for i in range(len(self.data)):
                        if self.data[i]["id"] == item["id"]:
                            self.data[i] = item
                            break
                ok = True
                self.formset.refresh_view(new_data=self.data)
            else:
                self.page.update()
                ok = False
            self.page.open(show_snackbar("Guardado" if ok else "Error al guardar", ok))
        except Exception as ex:
            print(f"[handle_submit_click] Error al guardar: {ex!r}")
            traceback.print_exc()
            raise


    def handle_delete_click(self, form):
        modal = CrudModal(self.page)
        modal.open(
            kind="delete",
            title="Eliminar usuario",
            content_controls=[ft.Text("¿Estás seguro de eliminar este registro?")],
            on_accept=lambda: self.delete_item(form),
            success_text="Usuario eliminado",
            error_text="Error al eliminar usuario",
            width=600,
        )

    def delete_item(self, form):
        self.formset.formset.remove(form)
        self.formset.refresh_view()
        return True

    def build_view_test(self) -> ft.Container:
        self.formset = Formset(self.page, self.form, self.data, self.actions, "Test", delete_button=self.delete_button)
        return self.formset.build_formset_view()
