def test_countries_are_seeded(api_client):
    resp = api_client.get("/countries", params={"limit": 50})
    assert resp.status_code == 200
    names = [c["text"] for c in resp.json()["results"].values()]
    assert "Costa Rica" in names


def test_abc_crud(api_client):
    created = api_client.post("/abc", params={"name": "Elemento"})
    assert created.status_code == 200, created.text
    item_id = created.json()["id"]

    updated = api_client.put(f"/abc/{item_id}", params={"name": "Elemento 2"})
    assert updated.status_code == 200, updated.text

    listing = api_client.get("/abc", params={"q": "Elemento 2"}).json()
    assert any(r["text"] == "Elemento 2" for r in listing["results"].values())

    assert api_client.delete(f"/abc/{item_id}").status_code == 200


def test_person_group_crud(api_client):
    country_id = int(next(iter(api_client.get("/countries").json()["results"])))
    person_ids = [int(k) for k in api_client.get("/persons").json()["results"]][:2]

    created = api_client.post("/persons_groups", json={
        "name": "Grupo de prueba", "country_id": country_id, "people_ids": person_ids, "community_ids": [],
    })
    assert created.status_code == 200, created.text
    group_id = created.json()["id"]

    detail = api_client.get(f"/persons_groups/{group_id}")
    assert detail.status_code == 200, detail.text

    listing = api_client.get("/persons_groups", params={"q": "prueba"}).json()
    assert str(group_id) in listing["results"]

    assert api_client.delete(f"/persons_groups/{group_id}").status_code == 200
    assert api_client.get(f"/persons_groups/{group_id}").status_code == 404
