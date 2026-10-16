import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from admin_api import app as admin_app

ADMIN = {"id": 1, "name": "Ann", "email": "ann@example.com", "role": "admin"}
MEMBER = {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "member"}


class FakeServers:
    """Stands in for the database so these tests need no Docker."""

    def __init__(self):
        self.added = []
        self.duplicate = False
        self.exists = True

    def list_servers(self):
        return [{"id": 1, "name": "currency", "enabled": True}]

    def add_server(self, name, url, credential=None):
        if self.duplicate:
            import psycopg

            raise psycopg.errors.UniqueViolation()
        self.added.append((name, url))
        return 7

    def set_enabled(self, server_id, enabled):
        return self.exists

    def delete_server(self, server_id):
        return self.exists


@pytest.fixture
def fake(monkeypatch):
    fake_servers = FakeServers()
    monkeypatch.setattr(admin_app, "servers", fake_servers)
    return fake_servers


def test_a_member_is_refused_before_any_server_endpoint_runs():
    with pytest.raises(HTTPException) as problem:
        admin_app.admin_only(MEMBER)
    assert problem.value.status_code == 403


def test_an_admin_can_list_servers(fake):
    assert admin_app.list_servers(ADMIN)[0]["name"] == "currency"


def test_adding_a_server_with_a_private_address_is_refused(fake, monkeypatch):
    monkeypatch.delenv("ALLOWED_UPSTREAM_HOSTS", raising=False)
    body = admin_app.NewServer(name="evil", url="http://169.254.169.254/")
    with pytest.raises(HTTPException) as problem:
        admin_app.add_server(body, ADMIN)
    assert problem.value.status_code == 400
    assert fake.added == []


def test_adding_a_server_with_an_allowed_address_works(fake, monkeypatch):
    monkeypatch.setenv("ALLOWED_UPSTREAM_HOSTS", "127.0.0.1")
    body = admin_app.NewServer(name="currency", url="http://127.0.0.1:8102/mcp")
    assert admin_app.add_server(body, ADMIN) == {"id": 7}
    assert fake.added == [("currency", "http://127.0.0.1:8102/mcp")]


def test_a_duplicate_name_gives_409(fake, monkeypatch):
    monkeypatch.setenv("ALLOWED_UPSTREAM_HOSTS", "127.0.0.1")
    fake.duplicate = True
    body = admin_app.NewServer(name="currency", url="http://127.0.0.1:8102/mcp")
    with pytest.raises(HTTPException) as problem:
        admin_app.add_server(body, ADMIN)
    assert problem.value.status_code == 409


@pytest.mark.parametrize("bad_name", ["has_underscore", "Capital", "with space", ""])
def test_server_names_must_be_lower_case_letters_and_digits(bad_name):
    with pytest.raises(ValidationError):
        admin_app.NewServer(name=bad_name, url="http://127.0.0.1:1/mcp")


def test_switching_or_deleting_a_missing_server_gives_404(fake):
    fake.exists = False
    with pytest.raises(HTTPException) as switch_problem:
        admin_app.switch_server(99, admin_app.EnabledFlag(enabled=False), ADMIN)
    assert switch_problem.value.status_code == 404
    with pytest.raises(HTTPException) as delete_problem:
        admin_app.remove_server(99, ADMIN)
    assert delete_problem.value.status_code == 404


def test_switching_and_deleting_an_existing_server_works(fake):
    assert admin_app.switch_server(1, admin_app.EnabledFlag(enabled=False), ADMIN) == {"enabled": False}
    assert admin_app.remove_server(1, ADMIN) == {"deleted": True}
