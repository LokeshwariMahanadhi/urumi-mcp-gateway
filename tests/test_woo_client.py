"""Tests for the WooCommerce client. These never talk to the real store."""
import os

import pytest
import httpx2
from servers.woocommerce.woo_client import WooClient, WooError, load_env_file, _error_text


def test_signed_url_has_a_signature_but_never_the_secret():
    client = WooClient("http://127.0.0.1:8081", "ck_test", "cs_super_secret")

    signed = client._signed_url(
        "GET", "http://127.0.0.1:8081/wp-json/wc/v3/orders", {"per_page": 5}
    )

    assert "oauth_signature=" in signed
    assert "oauth_consumer_key=ck_test" in signed
    assert "per_page=5" in signed
    # The secret signs the request but must never travel inside the URL.
    assert "cs_super_secret" not in signed


class FakeResponse:
    """A tiny stand-in for a store reply, so no network is needed."""

    def __init__(self, data=None, text=""):
        self._data = data
        self.text = text

    def json(self):
        if self._data is None:
            raise ValueError("not json")
        return self._data


def test_error_text_uses_the_store_message():
    reply = FakeResponse(data={"message": "Consumer key is invalid."})
    assert _error_text(reply) == "Consumer key is invalid."


def test_error_text_falls_back_to_plain_text():
    reply = FakeResponse(text="<html>Something broke</html>")
    assert "Something broke" in _error_text(reply)


def test_missing_setting_gives_a_clear_error(monkeypatch):
    # Give the client everything except the store address.
    monkeypatch.delenv("WOOCOMMERCE_URL", raising=False)
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_KEY", "ck_test")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_SECRET", "cs_test")

    with pytest.raises(WooError) as problem:
        WooClient.from_env()

    assert "WOOCOMMERCE_URL" in str(problem.value)


def test_env_file_fills_in_new_settings(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("MY_TEST_SETTING=hello\n")
    # Make sure the setting starts empty, and is cleaned up after the test.
    monkeypatch.setenv("MY_TEST_SETTING", "temporary")
    monkeypatch.delenv("MY_TEST_SETTING")

    load_env_file(env_file)

    assert os.environ["MY_TEST_SETTING"] == "hello"


def test_env_file_does_not_override_real_settings(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("MY_TEST_SETTING=from-file\n")
    monkeypatch.setenv("MY_TEST_SETTING", "from-shell")

    load_env_file(env_file)

    # A value already set outside the file wins.
    assert os.environ["MY_TEST_SETTING"] == "from-shell"
    

class FakeReply(FakeResponse):
    """A fake store reply that also has a status code."""

    def __init__(self, status_code, data=None, text=""):
        super().__init__(data=data, text=text)
        self.status_code = status_code


def pretend_store_answers(monkeypatch, outcome):
    """Swap the real HTTP client for a fake that returns or raises `outcome`."""

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def request(self, method, url, json=None):
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

    monkeypatch.setattr(httpx2, "AsyncClient", FakeAsyncClient)


def make_client():
    return WooClient("http://127.0.0.1:8081", "ck_test", "cs_test")


@pytest.mark.asyncio
async def test_good_answer_is_returned(monkeypatch):
    pretend_store_answers(monkeypatch, FakeReply(200, data={"id": 1}))
    assert await make_client().get("/orders") == {"id": 1}


@pytest.mark.asyncio
async def test_slow_store_becomes_a_timeout_message(monkeypatch):
    pretend_store_answers(monkeypatch, httpx2.TimeoutException("slow"))
    with pytest.raises(WooError) as problem:
        await make_client().get("/orders")
    assert "too long" in str(problem.value)


@pytest.mark.asyncio
async def test_store_down_becomes_a_clear_message(monkeypatch):
    pretend_store_answers(monkeypatch, httpx2.ConnectError("refused"))
    with pytest.raises(WooError) as problem:
        await make_client().get("/orders")
    assert "Could not reach the store" in str(problem.value)


@pytest.mark.asyncio
async def test_store_error_keeps_code_and_message(monkeypatch):
    reply = FakeReply(404, data={"message": "Invalid ID."})
    pretend_store_answers(monkeypatch, reply)
    with pytest.raises(WooError) as problem:
        await make_client().get("/orders/9999")
    assert "404" in str(problem.value)
    assert "Invalid ID." in str(problem.value)