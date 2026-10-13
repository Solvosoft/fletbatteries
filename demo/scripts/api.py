from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel

from fletbatteries.api import crud_router

import settings  # noqa: F401  (configura la base de datos por defecto)
from data.manager.abc_manager import ABCManager
from data.manager.community_manager import CommunityManager
from data.manager.country_manager import CountryManager
from data.manager.customer_manager import CustomerManager
from data.manager.person_group_manager import PersonGroupManager
from data.manager.person_manager import PersonManager
from data.manager.product_manager import ProductManager
from scripts.crud_router import create_crud_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Datos iniciales al arrancar la API
    ensure_initial_data()
    yield


app = FastAPI(lifespan=lifespan)

country_manager = CountryManager()
person_manager = PersonManager()
community_manager = CommunityManager()
person_group_manager = PersonGroupManager()
abc_manager = ABCManager()

# -----------------------------
# Endpoints select2 (formato {"results", "pagination"})
# -----------------------------
app.include_router(create_crud_router("countries", country_manager))
app.include_router(create_crud_router("persons", person_manager))
app.include_router(create_crud_router("communities", community_manager))
app.include_router(create_crud_router("abc", abc_manager))

# -----------------------------
# Endpoints REST genéricos de fletbatteries (los consume APISource)
# -----------------------------
app.include_router(crud_router(country_manager, prefix="/api/countries"))
app.include_router(crud_router(person_manager, prefix="/api/persons"))
app.include_router(crud_router(community_manager, prefix="/api/communities"))
app.include_router(crud_router(person_group_manager, prefix="/api/person_groups"))
app.include_router(crud_router(CustomerManager(), prefix="/api/customers"))
app.include_router(crud_router(ProductManager(), prefix="/api/products"))


# -----------------------------
# PersonGroup endpoints (formato anterior)
# -----------------------------
class PersonGroupSchema(BaseModel):
    name: str
    country_id: int
    people_ids: Optional[List[int]] = []
    community_ids: Optional[List[int]] = []


def group_to_dict(g):
    return {
        "id": g.id,
        "nombre": g.name,
        "Persons": [{"id": p.id, "name": p.name} for p in g.people],
        "Communities": [{"id": c.id, "name": c.name} for c in g.communities],
        "Country": {"id": g.country.id, "name": g.country.name} if g.country else None,
    }


@app.get("/persons_groups")
def get_person_groups(skip: int = Query(0, ge=0), limit: int = Query(5, ge=1), q: Optional[str] = Query(None)):
    page = person_group_manager.list(skip=skip, size=limit, search=q or "")
    results = {str(g.id): group_to_dict(g) for g in page.items}
    more = skip + limit < page.total
    return {"results": results, "pagination": {"more": more, "skip": skip, "limit": limit, "total": page.total}}


@app.get("/persons_groups/{group_id}")
def get_person_group(group_id: int = Path(..., ge=1)):
    group = person_group_manager.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group_to_dict(group)


@app.post("/persons_groups")
def add_person_group(item: PersonGroupSchema):
    try:
        group = person_group_manager.create(
            name=item.name, country_id=item.country_id, people=item.people_ids, communities=item.community_ids
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return group_to_dict(group)


@app.put("/persons_groups/{group_id}")
def update_person_group(group_id: int, item: PersonGroupSchema):
    try:
        group = person_group_manager.update(
            group_id, name=item.name, country_id=item.country_id, people=item.people_ids,
            communities=item.community_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return group_to_dict(group)


@app.delete("/persons_groups/{group_id}")
def delete_person_group(group_id: int):
    if not person_group_manager.delete(group_id):
        raise HTTPException(status_code=404, detail="PersonGroup not found")
    return {"message": "PersonGroup deleted successfully"}


# -----------------------------
# Datos iniciales
# Ejemplo: curl -X POST http://127.0.0.1:8000/countries/init
# -----------------------------
def _insert(manager, names):
    inserted = []
    for name in names:
        try:
            obj = manager.create(name=name)
            inserted.append({"id": obj.id, "name": obj.name})
        except ValueError:
            pass
    return inserted


@app.post("/countries/init")
def init_countries():
    latin_countries = [
        "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica",
        "Cuba", "República Dominicana", "Ecuador", "El Salvador", "Guatemala",
        "Honduras", "México", "Nicaragua", "Panamá", "Paraguay",
        "Perú", "Puerto Rico", "Uruguay", "Venezuela",
    ]
    return {"inserted": _insert(country_manager, latin_countries), "message": "Paises latinoamericanos insertados"}


@app.post("/persons/init")
def init_persons():
    names = [f"Persona {i}" for i in range(1, 11)]
    return {"inserted": _insert(person_manager, names), "message": "Personas iniciales insertadas"}


@app.post("/communities/init")
def init_communities():
    names = [f"Community {i}" for i in range(1, 11)]
    return {"inserted": _insert(community_manager, names), "message": "Communities iniciales insertadas"}


def ensure_initial_data():
    """Inicializa países, personas y comunidades si las tablas están vacías."""
    if not country_manager.count():
        init_countries()
    if not person_manager.count():
        init_persons()
    if not community_manager.count():
        init_communities()
