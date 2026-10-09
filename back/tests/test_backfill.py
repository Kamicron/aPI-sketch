from datetime import datetime

import pytest

from app.services import youtube
from tests.test_catalog import CHANNEL, add, auth, entry  # noqa: F401  (réutilise les aides du catalogue)


@pytest.fixture
def fake_youtube(monkeypatch):
    state = {"feed": [], "durations": {}}
    monkeypatch.setattr(youtube, "resolve_channel", lambda url: CHANNEL)
    monkeypatch.setattr(youtube, "fetch_feed", lambda channel_id: state["feed"])
    monkeypatch.setattr(youtube, "video_duration", lambda vid: state["durations"].get(vid))
    return state


def test_backfill_imports_history_in_batches(client, admin_token, fake_youtube, monkeypatch):
    cid = add(client, admin_token, min_duration_s=120, max_duration_s=1800).json()["id"]
    # 5 vidéos retenues, 1 trop courte, 1 trop longue ; "v0" est déjà connue via le flux RSS.
    listing = [youtube.ListedVideo(f"v{i}", f"Sketch {i}", 600) for i in range(5)]
    listing += [youtube.ListedVideo("court", "Court", 30), youtube.ListedVideo("long", "Long", 9000)]
    monkeypatch.setattr(youtube, "list_channel_videos", lambda channel_id, limit: listing)
    monkeypatch.setattr(
        youtube,
        "video_details",
        lambda vid: youtube.VideoDetails(vid, f"Titre {vid}", None, 600, datetime(2025, 1, int(vid[1:]) + 1), None),
    )
    fake_youtube["feed"] = [entry("v0", 1)]
    fake_youtube["durations"] = {"v0": 600}
    client.post(f"/api/comedians/{cid}/sync", headers=auth(admin_token))

    first = client.post(f"/api/comedians/{cid}/backfill?batch=2", headers=auth(admin_token)).json()
    assert first == {"discovered": 2, "filtered": 2, "remaining": 2}  # v1, v2 importées ; v3, v4 restent

    second = client.post(f"/api/comedians/{cid}/backfill?batch=10", headers=auth(admin_token)).json()
    assert second == {"discovered": 2, "filtered": 2, "remaining": 0}
    ids = [s["youtube_id"] for s in client.get("/api/sketches", headers=auth(admin_token)).json()]
    assert sorted(ids) == ["v0", "v1", "v2", "v3", "v4"]

    third = client.post(f"/api/comedians/{cid}/backfill", headers=auth(admin_token)).json()
    assert third["discovered"] == 0  # rien de nouveau : idempotent


def test_backfill_admin_only(client, admin_token, fake_youtube):
    cid = add(client, admin_token).json()["id"]
    invite = client.post("/api/invitations", json={}, headers=auth(admin_token)).json()
    member = client.post(
        "/api/auth/register",
        json={"code": invite["code"], "email": "m@test.fr", "username": "membre", "password": "password123"},
    ).json()["access_token"]
    assert client.post(f"/api/comedians/{cid}/backfill", headers=auth(member)).status_code == 403
