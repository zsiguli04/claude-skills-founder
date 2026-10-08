import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vagyonado_app.auth import hash_password
from vagyonado_app.config import DEFAULT_RULES_DIR, Settings
from vagyonado_app.db import Database, now
from vagyonado_app.web import create_app

PASSWORD = "correct horse battery"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(secret_key="x" * 40, database_path=tmp_path / "test.sqlite3",
                    rules_dir=DEFAULT_RULES_DIR, secure_cookies=False)


@pytest.fixture
def db(settings) -> Database:
    database = Database(settings.database_path)
    with database.connect() as conn:
        conn.execute("INSERT INTO users (email, name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                     ("anna@iroda.hu", "Anna", hash_password(PASSWORD), now()))
    return database


@pytest.fixture
def client(settings, db) -> TestClient:
    return TestClient(create_app(settings))


def csrf_of(html: str) -> str:
    match = re.search(r'name="csrf" value="([^"]+)"', html)
    assert match, "no CSRF token on the page"
    return match.group(1)


@pytest.fixture
def logged_in(client) -> TestClient:
    token = csrf_of(client.get("/login").text)
    r = client.post("/login", data={"csrf": token, "email": "anna@iroda.hu", "password": PASSWORD})
    assert r.status_code == 200 and "Ügyfelek" in r.text
    return client


def post(c: TestClient, url: str, data: dict, page: str = "/"):
    """Post a form with the CSRF token taken from a page, as a browser would."""
    return c.post(url, data={"csrf": csrf_of(c.get(page).text), **data})
