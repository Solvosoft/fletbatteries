"""
`ModelForm`: formulario generado a partir de un modelo SQLAlchemy.

    class CustomerForm(ModelForm):
        class Meta:
            model = Customer
            fields = ["name", "last_name", "email", "phone"]   # o exclude = [...]
            labels = {"last_name": "Apellidos"}
            widgets = {"phone": PhoneNumberMaskInput}

Los campos declarados en la clase reemplazan a los generados.
"""

import enum
from typing import Optional

import sqlalchemy as sa

from fletbatteries.forms import fields as f
from fletbatteries.forms.form import BaseForm, DeclarativeFieldsMetaclass
from fletbatteries.widgets.inputs import Textarea


def formfield_for_column(column: sa.Column, **overrides) -> Optional[f.Field]:
    """Crea el `Field` que corresponde a una columna (o `None` si no se puede editar)."""
    t = column.type
    required = not column.nullable and column.default is None and column.server_default is None
    kwargs = {"required": required}
    name = column.name.lower()

    if isinstance(t, sa.Enum):
        if t.enum_class is not None:
            choices = [(m.name if isinstance(m, enum.Enum) else m, getattr(m, "value", m)) for m in t.enum_class]
        else:
            choices = [(e, e) for e in t.enums]
        field = f.ChoiceField(choices=choices, **kwargs)
    elif isinstance(t, sa.Boolean):
        field = f.BooleanField()
    elif isinstance(t, sa.DateTime):
        field = f.DateTimeField(**kwargs)
    elif isinstance(t, sa.Date):
        field = f.DateField(**kwargs)
    elif isinstance(t, sa.Time):
        field = f.TimeField(**kwargs)
    elif isinstance(t, sa.Float):
        field = f.FloatField(**kwargs)
    elif isinstance(t, sa.Numeric):
        field = f.DecimalField(decimal_places=t.scale, **kwargs)
    elif isinstance(t, sa.Integer):
        field = f.IntegerField(**kwargs)
    elif isinstance(t, sa.Text):
        field = f.CharField(widget=Textarea, **kwargs)
    elif isinstance(t, sa.String):
        length = getattr(t, "length", None)
        if "email" in name:
            field = f.EmailField(max_length=length, **kwargs)
        elif "password" in name:
            field = f.PasswordField(max_length=length, **kwargs)
        else:
            field = f.CharField(max_length=length, **kwargs)
    else:
        return None
    for key, value in overrides.items():
        if value is not None:
            setattr(field, key, value)
    return field


def fields_for_model(model, fields=None, exclude=None, widgets=None, labels=None, help_texts=None) -> dict:
    result = {}
    columns = {c.key: c for c in sa.inspect(model).columns}
    names = fields if fields not in (None, "__all__") else list(columns)
    for name in names:
        if exclude and name in exclude:
            continue
        column = columns.get(name)
        if column is None:
            continue
        if column.primary_key and fields in (None, "__all__"):
            continue
        field = formfield_for_column(
            column,
            label=(labels or {}).get(name),
            help_text=(help_texts or {}).get(name),
        )
        if field is None:
            continue
        if widgets and name in widgets:
            field.widget = widgets[name]
        result[name] = field
    return result


class ModelFormMetaclass(DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(mcs, name, bases, attrs)
        meta = getattr(new_class, "Meta", None)
        model = getattr(meta, "model", None)
        if model is None:
            return new_class
        generated = fields_for_model(
            model,
            fields=getattr(meta, "fields", None),
            exclude=getattr(meta, "exclude", None),
            widgets=getattr(meta, "widgets", None),
            labels=getattr(meta, "labels", None),
            help_texts=getattr(meta, "help_texts", None),
        )
        declared = new_class.declared_fields
        merged = {}
        order = getattr(meta, "fields", None)
        names = list(order) if order not in (None, "__all__") else list(generated)
        for n in names:
            if n in declared:
                merged[n] = declared[n]
            elif n in generated:
                merged[n] = generated[n]
        for n, field in declared.items():
            merged.setdefault(n, field)
        for n, field in merged.items():
            if field.name is None:
                field.set_name(n)
        if getattr(new_class, "title", None) is None:
            new_class.title = getattr(meta, "verbose_name", None) or model.__name__
        new_class.base_fields = merged
        return new_class


class ModelForm(BaseForm, metaclass=ModelFormMetaclass):
    """Formulario ligado a un modelo SQLAlchemy (`Meta.model`)."""

    class Meta:
        model = None

    @property
    def model(self):
        return self.Meta.model

    def model_data(self) -> dict:
        """`cleaned_data` lista para el modelo (ver `save_data`)."""
        return self.save_data()

    def save(self, manager=None):
        """
        Crea o actualiza el registro. Con un `manager` (`BaseManager`/`DataSource`)
        se usa su `create`/`update`; sin él solo se aplican los valores a la instancia.
        """
        if not self.cleaned_data and self.errors == {}:
            self.full_clean()
        if self.errors:
            raise ValueError("El formulario tiene errores")
        data = self.model_data()
        pk = getattr(self.instance, "id", None) if self.instance is not None else None
        if manager is not None:
            obj = manager.update(pk, **data) if pk is not None else manager.create(**data)
        else:
            obj = self.instance if self.instance is not None else self.model()
            for key, value in data.items():
                setattr(obj, key, value)
        self.instance = obj
        return obj
