import pytest
from fastapi import HTTPException

from admin_api import app as admin_app

ADMIN = {"id": 1, "name": "Ann", "email": "ann@example.com", "role": "admin"}
MEMBER = {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "member"}


class FakeServers:
    def __init__(self):
        self.updated = None
        self.exists = True

    def update_server(self, server_id, url, credential=None):
        self.updated = (server_id, url, credential)
        return self.exists


def test_editing_a_server_keeps_the_credential_unless_a_new_one_is_given(monkeypatch):
    fake = FakeServers()
    monkeypatch.setattr(admin_app, "servers", fake)
    monkeypatch.setenv("ALLOWED_UPSTREAM_HOSTS", "127.0.0.1")
    assert admin_app.edit_server(1, admin_app.EditServer(url="http://127.0.0.1:9/mcp"), ADMIN) == {"updated": True}
    assert fake.updated == (1, "http://127.0.0.1:9/mcp", None)


def test_editing_a_server_to_a_private_address_is_refused(monkeypatch):
    fake = FakeServers()
    monkeypatch.setattr(admin_app, "servers", fake)
    monkeypatch.delenv("ALLOWED_UPSTREAM_HOSTS", raising=False)
    with pytest.raises(HTTPException) as problem:
        admin_app.edit_server(1, admin_app.EditServer(url="http://169.254.169.254/"), ADMIN)
    assert problem.value.status_code == 400
    assert fake.updated is None


def test_editing_a_missing_server_gives_404(monkeypatch):
    fake = FakeServers()
    fake.exists = False
    monkeypatch.setattr(admin_app, "servers", fake)
    monkeypatch.setenv("ALLOWED_UPSTREAM_HOSTS", "127.0.0.1")
    with pytest.raises(HTTPException) as problem:
        admin_app.edit_server(9, admin_app.EditServer(url="http://127.0.0.1:9/mcp"), ADMIN)
    assert problem.value.status_code == 404


def test_a_member_makes_a_key_only_for_themselves(monkeypatch):
    made = {}

    def fake_create_key(user_id, label):
        made["user_id"] = user_id
        return "urumi_fake"

    monkeypatch.setattr(admin_app, "create_key", fake_create_key)
    assert admin_app.make_my_key(admin_app.NewKey(label="laptop"), MEMBER) == {"key": "urumi_fake"}
    assert made["user_id"] == MEMBER["id"]


def test_a_member_sees_only_their_own_keys(monkeypatch):
    asked = {}

    def fake_list_keys_of(user_id):
        asked["user_id"] = user_id
        return []

    monkeypatch.setattr(admin_app.queries, "list_keys_of", fake_list_keys_of)
    admin_app.my_keys(MEMBER)
    assert asked["user_id"] == MEMBER["id"]


def test_a_member_cannot_revoke_someone_elses_key(monkeypatch):
    monkeypatch.setattr(admin_app, "revoke_own_key", lambda key_id, user_id: False)
    with pytest.raises(HTTPException) as problem:
        admin_app.revoke_my_key(5, MEMBER)
    assert problem.value.status_code == 404
