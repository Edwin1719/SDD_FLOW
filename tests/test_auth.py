"""Tests de la contraseña del panel (T16)."""

from datetime import timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.clocks import SystemClock
from app.db.repository import connect
from app.web.routes import router

UTC = timezone.utc


def _make_app(tmp_path, mode: str = "real"):
    repo = connect(tmp_path / "data" / "db.sqlite")
    app = FastAPI()
    app.state.mode = mode
    app.state.panel_password = "secreto"
    app.state.session_secret = "session-secret"
    app.state.repo = repo
    app.state.clinic_tz = UTC
    app.state.clock = SystemClock()
    app.include_router(router)
    return app, repo


def test_requires_login_without_session(tmp_path):
    app, repo = _make_app(tmp_path)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Acceso" in response.text
    repo.close()


def test_login_with_correct_password(tmp_path):
    app, repo = _make_app(tmp_path)
    client = TestClient(app)
    response = client.post("/login", data={"password": "secreto"})
    assert response.status_code == 200
    assert "Agenda" in response.text
    assert "session" in client.cookies
    repo.close()


def test_login_with_incorrect_password(tmp_path):
    app, repo = _make_app(tmp_path)
    client = TestClient(app)
    response = client.post("/login", data={"password": "incorrecta"})
    assert response.status_code == 200
    assert "Acceso" in response.text
    assert "session" not in client.cookies
    repo.close()


def test_demo_mode_skips_auth(tmp_path):
    app, repo = _make_app(tmp_path, mode="demo")
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Agenda" in response.text
    repo.close()
