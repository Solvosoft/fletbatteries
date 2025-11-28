from fastapi import APIRouter, Query, HTTPException

def create_crud_router(entity_name: str, manager):
    """
    Generic router for GET, POST, PUT, and DELETE of simple tables.
    The manager must have the following methods: get_all(), get_by_id(), create(), update(), delete()
    """
    router = APIRouter()

    @router.get(f"/{entity_name}")
    def get_items(skip: int = Query(0, ge=0), limit: int = Query(5, ge=1), q: str | None = Query(None, alias="q")):
        items = manager.get_all()
        if q:
            q_lower = q.lower()
            items = [i for i in items if q_lower in i.name.lower()]
        total = len(items)
        paginated = items[skip:skip+limit]
        results = {
            str(i.id): {"id": i.id, "text": i.name, "disabled": getattr(i, "disabled", False)}
            for i in paginated
        }
        more = skip + limit < total
        return {"results": results, "pagination": {"more": more, "skip": skip, "limit": limit, "total": total}}

    @router.post(f"/{entity_name}")
    def add_item(name: str):
        try:
            item = manager.create(name=name)
            return {"id": item.id, "name": item.name}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put(f"/{entity_name}/{{item_id}}")
    def update_item(item_id: int, name: str, disabled: bool | None = None):
        try:
            updated = manager.update(item_id, name=name, disabled=disabled)
            return {"id": updated.id, "name": updated.name, "disabled": getattr(updated, "disabled", False)}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.delete(f"/{entity_name}/{{item_id}}")
    def delete_item(item_id: int):
        try:
            manager.delete(item_id)
            return {"message": f"{entity_name[:-1]} deleted successfully"}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return router