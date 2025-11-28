from fastapi import FastAPI, Query, HTTPException, Path
from data.manager.country_manager import CountryManager
from data.manager.person_manager import PersonManager
from data.manager.community_manager import CommunityManager
from data.manager.person_group_manager import PersonGroupManager
from scripts.crud_router import create_crud_router
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

country_manager = CountryManager()
person_manager = PersonManager()
community_manager = CommunityManager()
person_group_manager = PersonGroupManager()

# -----------------------------
# Endpoints genéricos
# -----------------------------
app.include_router(create_crud_router("countries", country_manager))
app.include_router(create_crud_router("persons", person_manager))
app.include_router(create_crud_router("communities", community_manager))

# -----------------------------
# Endpoints específicos: PersonGroup
# -----------------------------
class PersonGroupSchema(BaseModel):
    name: str
    country_id: int
    people_ids: Optional[List[int]] = []
    community_ids: Optional[List[int]] = []

@app.get("/persons_groups")
def get_person_groups(skip: int = Query(0, ge=0), limit: int = Query(5, ge=1), q: Optional[str] = Query(None, alias="q")):
    groups = person_group_manager.get_all(eager=True)
    if q:
        q_lower = q.lower()
        groups = [g for g in groups if q_lower in g.name.lower()]
    total = len(groups)
    paginated = groups[skip:skip + limit]
    results = {}
    for g in paginated:
        results[str(g.id)] = {
            "id": g.id,
            "nombre": g.name,
            "Persons": [{"id": p.id, "name": p.name} for p in g.people],
            "Communities": [{"id": c.id, "name": c.name} for c in g.communities],
            "Country": {"id": g.country.id, "name": g.country.name} if g.country else None
        }
    more = skip + limit < total
    return {"results": results, "pagination": {"more": more, "skip": skip, "limit": limit, "total": total}}

@app.get("/persons_groups/{group_id}")
def get_person_group(group_id: int = Path(..., ge=1)):
    group = person_group_manager.get_by_id(group_id, eager=True)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {
        "id": group.id,
        "nombre": group.name,
        "Persons": [{"id": p.id, "name": p.name} for p in group.people],
        "Communities": [{"id": c.id, "name": c.name} for c in group.communities],
        "Country": {"id": group.country.id, "name": group.country.name} if group.country else None
    }

@app.post("/persons_groups")
def add_person_group(item: PersonGroupSchema):
    try:
        group = person_group_manager.create(
            name=item.name,
            country_id=item.country_id,
            people_ids=item.people_ids,
            community_ids=item.community_ids
        )
        return {
            "id": group.id,
            "nombre": group.name,
            "Persons": [{"id": p.id, "name": p.name} for p in group.people],
            "Communities": [{"id": c.id, "name": c.name} for c in group.communities],
            "Country": {"id": group.country.id, "name": group.country.name} if group.country else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/persons_groups/{group_id}")
def update_person_group(group_id: int, item: PersonGroupSchema):
    try:
        group = person_group_manager.update(
            group_id=group_id,
            name=item.name,
            country_id=item.country_id,
            people_ids=item.people_ids,
            community_ids=item.community_ids
        )

        # Devuelve el grupo actualizado
        return {
            "id": group.id,
            "nombre": group.name,
            "Persons": [{"id": p.id, "name": p.name} for p in group.people],
            "Communities": [{"id": c.id, "name": c.name} for c in group.communities],
            "Country": {"id": group.country.id, "name": group.country.name} if group.country else None
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/persons_groups/{group_id}")
def delete_person_group(group_id: int):
    try:
        person_group_manager.delete(group_id)
        return {"message": "PersonGroup deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# -----------------------------
# Insert presets
# Example of use:
# curl -X POST http://127.0.0.1:8000/persons/init
# -----------------------------
@app.post("/countries/init")
def init_countries():
    latin_countries = [
        "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica",
        "Cuba", "República Dominicana", "Ecuador", "El Salvador", "Guatemala",
        "Honduras", "México", "Nicaragua", "Panamá", "Paraguay",
        "Perú", "Puerto Rico", "Uruguay", "Venezuela"
    ]
    inserted = []
    for name in latin_countries:
        try:
            country = country_manager.create_country(name=name)
            inserted.append({"id": country.id, "name": country.name})
        except ValueError:
            pass
    return {"inserted": inserted, "message": "Paises latinoamericanos insertados"}

@app.post("/persons/init")
def init_persons():
    initial_persons = [f"Persona {i}" for i in range(1, 11)]
    inserted = []
    for name in initial_persons:
        try:
            person = person_manager.create_person(name=name)
            inserted.append({"id": person.id, "name": person.name})
        except ValueError:
            pass
    return {"inserted": inserted, "message": "Personas iniciales insertadas"}

@app.post("/communities/init")
def init_communities():
    initial_communities = [f"Community {i}" for i in range(1, 11)]
    inserted = []
    for name in initial_communities:
        try:
            community = community_manager.create_community(name=name)
            inserted.append({"id": community.id, "name": community.name})
        except ValueError:
            pass
    return {"inserted": inserted, "message": "Communities iniciales insertadas"}
