from fastapi import APIRouter, Query, HTTPException


def create_crud_router(entity_name: str, manager):
    """
    Generic router for GET, POST, PUT, and DELETE of simple tables.
    Formato select2 ({"results", "pagination"}) con altas y cambios por query params.
    El manager es un `BaseManager` de fletbatteries.
    """
    router = APIRouter()

    @router.get(f"/{entity_name}")
    def get_items(skip: int = Query(0, ge=0), limit: int = Query(5, ge=1), q: str | None = Query(None, alias="q")):
        page = manager.list(skip=skip, size=limit, search=q or "")
        total = page.total
        paginated = page.items
        results = {
            str(i.id): {
                "id": i.id,
                "text": i.name,
                "disabled": getattr(i, "disabled", False)
            }
            for i in paginated
        }
        more = skip + limit < total
        return {
            "results": results,
            "pagination": {
                "more": more,
                "skip": skip,
                "limit": limit,
                "total": total
            }
        }

    @router.post(f"/{entity_name}")
    def add_item(name: str, disabled: bool = False):
        try:
            item = manager.create(name=name, disabled=disabled)
            return {
                "id": item.id,
                "name": item.name,
                "disabled": getattr(item, "disabled", False)
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put(f"/{entity_name}/{{item_id}}")
    def update_item(item_id: int, name: str = None, disabled: bool = None):
        try:
            update_kwargs = {}
            if name is not None:
                update_kwargs['name'] = name
            if disabled is not None:
                update_kwargs['disabled'] = disabled

            updated = manager.update(item_id, **update_kwargs)
            return {
                "id": updated.id,
                "name": updated.name,
                "disabled": getattr(updated, "disabled", False)
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.delete(f"/{entity_name}/{{item_id}}")
    def delete_item(item_id: int):
        if not manager.delete(item_id):
            raise HTTPException(status_code=404, detail=f"{entity_name} {item_id} not found")
        return {"message": f"{entity_name[:-1]} deleted successfully"}

    return router