def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["db"] == "up"


def test_login_wrong_password(client, admin_token):
    res = client.post("/api/auth/login", json={"login": "admin", "password": "nope-nope"})
    assert res.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_invite_then_register(client, admin_token):
    inv = client.post("/api/invitations", json={}, headers=auth(admin_token)).json()
    assert inv["status"] == "pending"
    assert client.get(f"/api/auth/invitations/{inv['code']}").json()["valid"] is True

    res = client.post(
        "/api/auth/register",
        json={"code": inv["code"], "email": "Bob@test.fr", "username": "bob", "password": "password123"},
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    me = client.get("/api/auth/me", headers=auth(token)).json()
    assert me["email"] == "bob@test.fr" and me["is_admin"] is False

    # Invitation à usage unique
    again = client.post(
        "/api/auth/register",
        json={"code": inv["code"], "email": "eve@test.fr", "username": "eve", "password": "password123"},
    )
    assert again.status_code == 400


def test_register_without_valid_code(client):
    res = client.post(
        "/api/auth/register",
        json={"code": "bidon", "email": "x@test.fr", "username": "xxx", "password": "password123"},
    )
    assert res.status_code == 400


def test_invitation_reserved_to_email(client, admin_token):
    inv = client.post("/api/invitations", json={"email": "ok@test.fr"}, headers=auth(admin_token)).json()
    bad = client.post(
        "/api/auth/register",
        json={"code": inv["code"], "email": "other@test.fr", "username": "other", "password": "password123"},
    )
    assert bad.status_code == 400


def test_revoke_invitation(client, admin_token):
    inv = client.post("/api/invitations", json={}, headers=auth(admin_token)).json()
    assert client.delete(f"/api/invitations/{inv['id']}", headers=auth(admin_token)).status_code == 204
    assert client.get(f"/api/auth/invitations/{inv['code']}").json()["valid"] is False
    listed = client.get("/api/invitations", headers=auth(admin_token)).json()
    assert listed[0]["status"] == "revoked"
