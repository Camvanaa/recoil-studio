from fastapi.testclient import TestClient

from app.core.app_factory import create_app

client = TestClient(create_app())


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recalculate_pattern_endpoint():
    response = client.post(
        "/api/pattern/recalculate",
        json={
            "points": [{"x": 100, "y": 400}, {"x": 95, "y": 375}],
            "scale_x": 1,
            "scale_y": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["pattern"] == [{"y": 25.0, "x": 5.0}]


def test_generate_lua_endpoint_requires_at_least_one_gun():
    response = client.post("/api/lua/generate", json={"guns": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "至少需要一个枪械配置"


def test_list_script_targets_endpoint():
    response = client.get("/api/lua/targets")

    assert response.status_code == 200
    assert response.json() == [{"id": "logitech-ghub-lua", "name": "Logitech G HUB Lua"}]


def test_generate_lua_endpoint_uses_target_id():
    response = client.post(
        "/api/lua/generate",
        json={
            "target_id": "logitech-ghub-lua",
            "guns": [{"name": "AK", "pattern": [{"y": 1, "x": 2}]}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert 'name = "AK"' in body["lua_code"]


def test_preview_patch_endpoint():
    response = client.post(
        "/api/patches/preview",
        json={
            "pattern": [{"y": 10, "x": 2}],
            "guns": [],
            "patch": {
                "id": "scale",
                "title": "Scale pattern",
                "operations": [
                    {"type": "transform-pattern", "target": "pattern", "scale_y": 2}
                ],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["changes"][0]["before"] == [{"y": 10.0, "x": 2.0}]
    assert body["changes"][0]["after"] == [{"y": 20.0, "x": 2.0}]


def test_apply_patch_endpoint_rejects_invalid_patch():
    response = client.post(
        "/api/patches/apply",
        json={
            "pattern": [],
            "guns": [],
            "patch": {"id": "empty", "title": "Empty", "operations": []},
        },
    )

    assert response.status_code == 400
    assert "at least one operation" in response.json()["detail"]


def test_task_lifecycle_endpoints():
    created = client.post("/api/tasks", json={"type": "pattern-detection", "payload": {}})

    assert created.status_code == 200
    task = created.json()
    assert task["status"] == "queued"

    fetched = client.get(f"/api/tasks/{task['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == task["id"]

    cancelled = client.post(f"/api/tasks/{task['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_data_file_list_endpoint():
    response = client.get("/api/data")

    assert response.status_code == 200
    assert any(item["path"] == "m14.lua" for item in response.json())


def test_data_file_import_endpoint():
    response = client.get("/api/data/m14.lua")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "m14"
    assert body["pattern"][0] == {"y": 45.0, "x": -5.5}
