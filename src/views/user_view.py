import flet as ft

from controls.user.user_control import UserControl
from components.shared.formset import Formset
from controls.utils import get_form, show_snackbar
from components.shared.modals import CrudModal

"""Initializes the user view.
page: instance of ft.Page.
forms: forms collection; selects "UserForm".
Sets up actions (Save button) and delete_button (Delete button) as factories that receive form.
Creates UserControl and CrudModal.
Note: on_click uses ft=form; this may collide with the Flet module alias. Prefer form=form."""
class UserView:
    def __init__(self, page: ft.Page, forms: []):
        self.page = page
        self.control = UserControl()
        self.form = get_form(forms, "UserForm")
        self.formset = None
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

    """Opens a confirmation modal to delete a user.
    Builds a "delete" CrudModal.
    Calls delete_user(form) in on_accept.
    Shows success/error messages and sets the modal width."""
    def handle_delete_click(self, form):
        modal = CrudModal(self.page)
        modal.open(
            kind="delete",
            title="Eliminar usuario",
            content_controls=[ft.Text("¿Estás seguro de eliminar este registro?")],
            on_accept=lambda: self.delete_user(form),
            success_text="Usuario eliminado",
            error_text="Error al eliminar usuario",
            width=600,
        )

    """Handles the Save click.
    Calls submit(form) and gets a boolean result.
    Shows a SnackBar indicating success or failure.
    Refreshes the view (self.formset.refresh_view())."""
    def handle_submit_click(self,form):
        ok = self.submit(form)
        self.page.open(show_snackbar("Guardado" if ok else "Error al guardar", ok))
        self.formset.refresh_view()

    """Submits (creates/updates) a user based on form state.
    Validates with form.is_valid().
    Gets item = form.get_item().
    If item["id"] is 0 or None, creates; otherwise updates.
    Returns True on success; if invalid, refreshes view and returns False.
    On exception, prints the error (consider returning False).
    Note: there is a self.formset.refresh_view(new_data=...) after a return that will never run."""
    def submit(self, form):
        try:
            if form.is_valid():
                item = form.get_item()
                if item["id"] == 0 or item["id"] is None:
                    self.control.create_user(item["name"], item["email"], item["password"])
                else:
                    self.control.update_user(item["id"], item["name"], item["email"], item["password"])
                return True
            else:
                self.formset.refresh_view()
                return False
            self.formset.refresh_view(new_data=self.get_all_users())
        except Exception as ex:
            print(f"Error al guardar usuario: {ex}")

    """Fetches all users from UserControl.
    Returns the user list/data to populate the view."""
    def get_all_users(self):
        return self.control.get_all_users()

    """Deletes a user using the id taken from the form.
    After deletion, refreshes the view with updated data.
    Returns True if the deletion is triggered successfully."""
    def delete_user(self, form):
        self.control.delete_user(form.get_item()["id"])
        self.formset.refresh_view(new_data=self.get_all_users())
        return True

    """Builds and returns the main users view.
    Creates a Formset with the page, form, current data, actions, the title "Usuarios", and the delete_button.
    Returns the container produced by formset.build_formset_view()."""
    def build_view_user(self) -> ft.Container:
        self.formset = Formset(self.page, self.form, self.get_all_users(), self.actions, "Usuarios",delete_button=self.delete_button)
        return self.formset.build_formset_view()
