"""Formularios y CRUDs de prueba de la librería."""

from fletbatteries import forms
from fletbatteries.crud import ACTIONS, CRUDView
from fletbatteries.data import SQLAlchemySource

from tests_lib.models import CategoryManager, DocManager, Item, ItemManager

KINDS = [("a", "Tipo A"), ("b", "Tipo B")]


class ItemForm(forms.ModelForm):
    title = "Item"
    kind = forms.ChoiceField(label="Tipo", choices=KINDS, required=False)

    class Meta:
        model = Item
        fields = ["name", "code", "price", "active", "kind", "category_id"]
        labels = {"name": "Nombre", "code": "Código", "price": "Precio", "category_id": "Categoría"}


class ItemCRUD(CRUDView):
    title = "Items"
    name = "item"
    manager = ItemManager()
    form_class = ItemForm
    list_fields = ["name", "code", "price", "kind", "category_id"]
    filter_fields = ["name"]
    actions = ACTIONS + ("clone",)
    bulk_delete = True
    export = True
    importable = True
    import_key_field = "code"


class DocForm(forms.Form):
    title = forms.CharField(label="Título", max_length=60)


class DocCRUD(CRUDView):
    title = "Docs"
    name = "doc"
    manager = DocManager()
    form_class = DocForm
    list_fields = ["title"]


def category_source():
    return SQLAlchemySource(CategoryManager())
