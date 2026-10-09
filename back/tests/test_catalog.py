from datetime import datetime

import pytest

from app.db import SessionLocal
from app.models import Comedian, Sketch
from app.services import catalog, youtube

CHANNEL = youtube.ChannelInfo("UCabc123", "Gaspard Proust", "https://www.youtube.com/channel/UCabc123")


def entry(video_id, day=1):
    return youtube.FeedEntry(video_id, "Sketch", datetime(2026, 1, day), f"https://i.ytimg.com/{video_id}.jpg", "desc")


@pytest.fixture
def fake_youtube(monkeypatch):
    state = {"feed": [], "durations": {}}
    monkeypatch.setattr(youtube, "resolve_channel", lambda url: CHANNEL)
    monkeypatch.setattr(youtube, "fetch_feed", lambda channel_id: state["feed"])
    monkeypatch.setattr(youtube, "video_duration", lambda vid: state["durations"].get(vid))
    return state


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def add(client, token, **body):
    return client.post("/api/comedians", json={"channel_url": "https://www.youtube.com/@x", **body}, headers=auth(token))


def test_add_comedian_admin_only(client, admin_token, fake_youtube):
    invite = client.post("/api/invitations", json={}, headers=auth(admin_token)).json()
    member = client.post(
        "/api/auth/register",
        json={"code": invite["code"], "email": "m@test.fr", "username": "membre", "password": "password123"},
    ).json()["access_token"]
    assert add(client, member).status_code == 403
    res = add(client, admin_token)
    assert res.status_code == 201
    assert res.json()["name"] == "Gaspard Proust" and res.json()["sketch_count"] == 0
    assert add(client, admin_token).status_code == 409  # déjà suivie
    assert [c["name"] for c in client.get("/api/comedians", headers=auth(member)).json()] == ["Gaspard Proust"]


def test_invalid_duration_range(client, admin_token, fake_youtube):
    assert add(client, admin_token, min_duration_s=600, max_duration_s=60).status_code == 422


def test_unknown_channel(client, admin_token, monkeypatch):
    def boom(url):
        raise youtube.YouTubeError("Chaîne introuvable")

    monkeypatch.setattr(youtube, "resolve_channel", boom)
    res = add(client, admin_token)
    assert res.status_code == 400 and res.json()["detail"] == "Chaîne introuvable"


def test_sync_filters_by_duration_and_is_incremental(client, admin_token, fake_youtube):
    cid = add(client, admin_token, min_duration_s=120, max_duration_s=1800).json()["id"]
    fake_youtube["feed"] = [entry("short", 1), entry("good", 2), entry("long", 3), entry("live", 4)]
    fake_youtube["durations"] = {"short": 45, "good": 600, "long": 7200}  # "live" : durée inconnue

    res = client.post(f"/api/comedians/{cid}/sync", headers=auth(admin_token))
    assert res.json() == {"discovered": 1, "filtered": 3}

    sketches = client.get("/api/sketches", headers=auth(admin_token)).json()
    assert [s["youtube_id"] for s in sketches] == ["good"]
    assert client.get("/api/comedians", headers=auth(admin_token)).json()[0]["sketch_count"] == 1

    # Deuxième passe : seule la nouveauté est examinée, les vidéos filtrées ne sont pas réévaluées.
    fake_youtube["feed"].append(entry("fresh", 5))
    fake_youtube["durations"] = {"short": 600, "fresh": 300}
    res = client.post(f"/api/comedians/{cid}/sync", headers=auth(admin_token))
    assert res.json() == {"discovered": 1, "filtered": 0}
    ids = [s["youtube_id"] for s in client.get("/api/sketches", headers=auth(admin_token)).json()]
    assert ids == ["fresh", "good"]  # plus récent d'abord


def test_update_and_delete_comedian(client, admin_token, fake_youtube):
    cid = add(client, admin_token).json()["id"]
    fake_youtube["feed"] = [entry("good")]
    fake_youtube["durations"] = {"good": 600}
    client.post(f"/api/comedians/{cid}/sync", headers=auth(admin_token))

    res = client.patch(
        f"/api/comedians/{cid}", json={"subscribed": False, "max_duration_s": 3600}, headers=auth(admin_token)
    )
    assert res.json()["subscribed"] is False and res.json()["max_duration_s"] == 3600
    assert client.patch(f"/api/comedians/{cid}", json={"min_duration_s": 9999}, headers=auth(admin_token)).status_code == 422

    assert client.delete(f"/api/comedians/{cid}", headers=auth(admin_token)).status_code == 204
    with SessionLocal() as db:
        assert db.query(Comedian).count() == 0
        assert db.query(Sketch).count() == 0  # suppression en cascade


def test_sync_all_isolates_failures(client, admin_token, fake_youtube, monkeypatch):
    add(client, admin_token)

    def boom(channel_id):
        raise youtube.YouTubeError("Flux RSS indisponible")

    monkeypatch.setattr(youtube, "fetch_feed", boom)
    with SessionLocal() as db:
        assert catalog.sync_all(db) == {"Gaspard Proust": "Flux RSS indisponible"}


def test_resolve_channel_rejects_other_sites():
    with pytest.raises(youtube.YouTubeError):
        youtube.resolve_channel("https://example.com/@x")
    with pytest.raises(youtube.YouTubeError):
        youtube.resolve_channel("file:///etc/passwd")
