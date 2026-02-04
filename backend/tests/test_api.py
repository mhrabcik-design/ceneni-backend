import pytest

def test_status_endpoint(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "total_items" in data

def test_add_item_and_search(client):
    # 1. Add a custom item
    add_resp = client.post("/items/add", json={
        "name": "Test Kabel CYKY 3x1.5",
        "price_material": 15.5,
        "price_labor": 10.0,
        "unit": "m"
    })
    assert add_resp.status_code == 200
    item_id = add_resp.json()["item_id"]

    # 2. Search for it
    search_resp = client.get(f"/search?q=Kabel")
    assert search_resp.status_code == 200
    items = search_resp.json()
    assert any(it["id"] == item_id for it in items)

def test_matching_with_alias(client):
    # 1. Ensure item exists
    add_resp = client.post("/items/add", json={
        "name": "Sádrokartonová deska bílá",
        "price_material": 100.0,
        "item_id_ext": "sdk-001"
    })
    item_id = add_resp.json()["item_id"]

    # 2. Search for unknown term (should fail or have low score)
    query = "bílej papundekl"
    match_resp = client.post("/match", json={"items": [query], "threshold": 0.4})
    assert match_resp.status_code == 200
    assert query not in match_resp.json() or match_resp.json()[query] is None

    # 3. Learn alias
    learn_resp = client.post("/feedback/learn", json={
        "query": query,
        "item_id": item_id
    })
    assert learn_resp.status_code == 200

    # 4. Search again (should match with high score)
    match_resp_2 = client.post("/match", json={"items": [query], "threshold": 0.4})
    assert match_resp_2.status_code == 200
    results = match_resp_2.json()
    assert query in results
    assert results[query]["item_id"] == item_id
    assert results[query]["match_score"] >= 0.8

def test_admin_alias_management(client):
    # Check if aliases appear in management
    resp = client.get("/admin/aliases")
    assert resp.status_code == 200
    aliases = resp.json()
    assert len(aliases) > 0
    alias_id = aliases[0]["id"]

    # Delete the alias
    del_resp = client.post("/admin/aliases/batch-delete", json=[alias_id])
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] == 1

    # verify deleted
    resp_2 = client.get("/admin/aliases")
    assert not any(al["id"] == alias_id for al in resp_2.json())
