from pathlib import Path

from app import create_app


def create_test_client(tmp_path: Path):
    database_path = tmp_path / "test.sqlite3"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database_path),
            "SECRET_KEY": "test-secret",
        }
    )
    return app.test_client()


def test_register_login_and_history_persistence(tmp_path):
    client = create_test_client(tmp_path)

    register_response = client.post(
        "/api/auth/register",
        json={"username": "alumno", "password": "secreto123"},
    )
    assert register_response.status_code == 200
    assert register_response.get_json()["user"]["username"] == "alumno"

    save_response = client.post(
        "/api/history",
        json={
            "label": "Mi practica",
            "grammar": "<S> ::= a",
            "inputs": "a",
            "start_symbol": "<S>",
            "derivation_mode": "leftmost",
        },
    )
    assert save_response.status_code == 200
    saved_entry = save_response.get_json()["entry"]
    assert saved_entry["label"] == "Mi practica"

    history_response = client.get("/api/history")
    history_payload = history_response.get_json()
    assert history_response.status_code == 200
    assert len(history_payload["entries"]) == 1
    assert history_payload["entries"][0]["grammar"] == "<S> ::= a"

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    unauthorized_history = client.get("/api/history")
    assert unauthorized_history.status_code == 401

    login_response = client.post(
        "/api/auth/login",
        json={"username": "alumno", "password": "secreto123"},
    )
    assert login_response.status_code == 200

    history_after_login = client.get("/api/history")
    assert history_after_login.status_code == 200
    assert len(history_after_login.get_json()["entries"]) == 1
