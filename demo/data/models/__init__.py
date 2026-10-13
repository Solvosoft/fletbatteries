# Importa todos los modelos para que SQLAlchemy pueda resolver las relaciones
# declaradas por nombre (p. ej. PersonGroup -> "Country") en cualquier proceso.
from data.models import (  # noqa: F401
    abc,
    calendar_event,
    community,
    country,
    customer,
    note,
    person,
    person_group,
    product,
    user,
)
