from fastapi import FastAPI, Query
from data.manager.country_manager import CountryManager
from data.manager.person_manager import PersonManager

app = FastAPI()

country_manager = CountryManager()
person_manager = PersonManager()


# -----------------------------
# EndPoints con búsqueda
# -----------------------------
@app.get("/countries")
def get_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1),
    search: str | None = Query(None, alias="q")  # ahora acepta 'search' o 'q'
):
    countries = country_manager.get_all_countries()

    # Filtrado por búsqueda
    if search:
        search_lower = search.lower()
        countries = [c for c in countries if search_lower in c.name.lower()]

    total = len(countries)
    paginated = countries[skip:skip + limit]

    results = {
        str(c.id): {"id": c.id, "text": c.name, "disabled": c.disabled, "selected": c.selected}
        for c in paginated
    }

    more = skip + limit < total
    return {
        "results": results,
        "pagination": {"more": more, "skip": skip, "limit": limit, "total": total}
    }


@app.post("/countries")
def add_country(name: str):
    try:
        country = country_manager.create_country(name=name)
        return {"id": country.id, "name": country.name}
    except ValueError as e:
        return {"error": str(e)}


@app.get("/persons")
def get_persons(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1),
    search: str | None = Query(None, alias="q")  # ahora acepta 'search' o 'q'
):
    persons = person_manager.get_all_persons()

    # Filtrado por búsqueda
    if search:
        search_lower = search.lower()
        persons = [p for p in persons if search_lower in p.name.lower()]

    total = len(persons)
    paginated = persons[skip:skip + limit]

    results = {
        str(p.id): {"id": p.id, "text": p.name, "disabled": p.disabled, "selected": p.selected}
        for p in paginated
    }

    more = skip + limit < total
    return {
        "results": results,
        "pagination": {"more": more, "skip": skip, "limit": limit, "total": total}
    }


@app.post("/persons")
def add_person(name: str):
    try:
        person = person_manager.create_person(name=name)
        return {"id": person.id, "name": person.name}
    except ValueError as e:
        return {"error": str(e)}


# -----------------------------
# Insert presets
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
