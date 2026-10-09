from datetime import datetime

import pytest

from app.db import SessionLocal
from app.models import Comedian, Like, Sketch


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sketch_id():
    with SessionLocal() as db:
        c = Comedian(name="Humoriste", youtube_channel_id="UC1", channel_url="https://www.youtube.com/channel/UC1")
        db.add(c)
        db.flush()
        ok = Sketch(comedian_id=c.id, youtube_id="vid1", title="Bon", duration_s=300, published_at=datetime(2026, 1, 1))
        hidden = Sketch(comedian_id=c.id, youtube_id="vid2", title="Hors filtre", duration_s=10,
                        published_at=datetime(2026, 1, 2), status="filtered")
        db.add_all([ok, hidden])
        db.commit()
        return ok.id, hidden.id


@pytest.fixture
def member_token(client, admin_token):
    code = client.post("/api/invitations", json={}, headers=auth(admin_token)).json()["code"]
    res = client.post("/api/auth/register", json={"code": code, "email": "m@test.fr", "username": "membre", "password": "password123"})
    return res.json()["access_token"]


def test_like_unlike_and_list(client, admin_token, sketch_id):
    sid, _ = sketch_id
    assert client.get("/api/sketches", headers=auth(admin_token)).json()[0]["liked"] is False
    assert client.put(f"/api/sketches/{sid}/like", headers=auth(admin_token)).status_code == 204
    assert client.put(f"/api/sketches/{sid}/like", headers=auth(admin_token)).status_code == 204  # idempotent

    listed = client.get("/api/sketches", headers=auth(admin_token)).json()[0]
    assert listed["liked"] is True and listed["comedian_name"] == "Humoriste"
    assert [s["id"] for s in client.get("/api/me/likes", headers=auth(admin_token)).json()] == [sid]

    assert client.delete(f"/api/sketches/{sid}/like", headers=auth(admin_token)).status_code == 204
    assert client.delete(f"/api/sketches/{sid}/like", headers=auth(admin_token)).status_code == 204
    assert client.get("/api/me/likes", headers=auth(admin_token)).json() == []


def test_likes_are_personal(client, admin_token, member_token, sketch_id):
    sid, _ = sketch_id
    client.put(f"/api/sketches/{sid}/like", headers=auth(admin_token))
    assert client.get("/api/me/likes", headers=auth(member_token)).json() == []
    assert client.get("/api/sketches", headers=auth(member_token)).json()[0]["liked"] is False
    with SessionLocal() as db:
        assert db.query(Like).count() == 1


def test_filtered_or_unknown_sketch_is_404(client, admin_token, sketch_id):
    _, hidden = sketch_id
    assert client.put(f"/api/sketches/{hidden}/like", headers=auth(admin_token)).status_code == 404
    assert client.post(f"/api/sketches/{hidden}/play", headers=auth(admin_token)).status_code == 404
    assert client.post("/api/sketches/9999/play", headers=auth(admin_token)).status_code == 404


def test_history_most_recent_first_and_counts(client, admin_token, sketch_id):
    sid, _ = sketch_id
    with SessionLocal() as db:
        other = Sketch(comedian_id=db.query(Comedian).first().id, youtube_id="vid3", title="Autre", duration_s=200,
                       published_at=datetime(2026, 1, 3))
        db.add(other)
        db.commit()
        other_id = other.id
    for s in (sid, other_id, sid):
        assert client.post(f"/api/sketches/{s}/play", headers=auth(admin_token)).status_code == 204
    history = client.get("/api/me/history", headers=auth(admin_token)).json()
    assert [h["id"] for h in history] == [sid, other_id]  # sid réécouté en dernier, sans doublon


def test_library_requires_auth(client, sketch_id):
    sid, _ = sketch_id
    assert client.get("/api/me/likes").status_code == 401
    assert client.put(f"/api/sketches/{sid}/like").status_code == 401
    assert client.post(f"/api/sketches/{sid}/play").status_code == 401
