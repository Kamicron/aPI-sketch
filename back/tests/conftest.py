import os

# Base SQLite jetable : doit être posé avant tout import de app.*
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    with SessionLocal() as db:
        db.add(User(email="admin@test.fr", username="admin", password_hash=hash_password("password123"), is_admin=True))
        db.commit()
    res = client.post("/api/auth/login", json={"login": "admin", "password": "password123"})
    return res.json()["access_token"]
