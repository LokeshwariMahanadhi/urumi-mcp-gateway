"""The gateway only answers requests addressed to host names we allow."""
from gateway.server import transport_security


def test_local_names_are_always_allowed(monkeypatch):
    monkeypatch.delenv("ALLOWED_MCP_HOSTS", raising=False)
    settings = transport_security()
    assert "localhost:*" in settings.allowed_hosts
    assert "gateway" not in settings.allowed_hosts


def test_extra_names_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("ALLOWED_MCP_HOSTS", "gateway, urumi.example.com")
    settings = transport_security()
    assert "gateway:*" in settings.allowed_hosts
    assert "urumi.example.com" in settings.allowed_hosts
    assert "https://urumi.example.com" in settings.allowed_origins
    assert settings.enable_dns_rebinding_protection is True
