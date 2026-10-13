import flet as ft

from fletbatteries.crud import CRUDView

from app_forms import CustomerForm
from data.manager.customer_manager import CustomerManager


class CustomerCRUD(CRUDView):
    title = "Customers"
    name = "cliente"
    manager = CustomerManager()
    form_class = CustomerForm
    list_fields = ["name", "last_name", "email", "phone"]
    filter_fields = ["name", "email"]
    selectable = True


def build_view_customer(page: ft.Page) -> ft.Control:
    return CustomerCRUD(page).build()


def build_view_customer_detail(page: ft.Page, id: str) -> ft.Control:
    """Ruta con parámetro: /customers/:id."""
    crud = CustomerCRUD(page)
    item = crud.source.get(int(id)) if id.isdigit() else None
    if item is None:
        return ft.Text("Cliente no encontrado", key="customer_not_found")
    return ft.Container(
        padding=10,
        content=ft.Column([ft.Text(f"{item['name']} {item['last_name'] or ''}", size=20, key="customer_title"),
                           *crud.detail_controls(item)]),
    )
