"""Small client for the WooCommerce REST API.

The store runs on plain HTTP, and WooCommerce only accepts Basic auth over
HTTPS. So every request here is signed with OAuth 1.0a instead.
"""
import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path
from urllib.parse import quote

import httpx2


class WooError(Exception):
    """Raised when the store is unreachable or answers with an error."""


def load_env_file(path):
    """Copy NAME=value lines from a .env file into the environment.

    Values that are already set win, so Docker and Kubernetes can override.
    """
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip())


def _error_text(response):
    """Pull a short, safe message out of an error reply."""
    try:
        return response.json().get("message", "no details")
    except Exception:
        return response.text[:200]


class WooClient:
    def __init__(self, store_url, consumer_key, consumer_secret, timeout=10.0):
        self.store_url = store_url.rstrip("/")
        self.api_url = self.store_url + "/wp-json/wc/v3"
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.timeout = timeout

    @classmethod
    def from_env(cls):
        """Build a client from the WOOCOMMERCE_* environment variables."""
        try:
            return cls(
                os.environ["WOOCOMMERCE_URL"],
                os.environ["WOOCOMMERCE_CONSUMER_KEY"],
                os.environ["WOOCOMMERCE_CONSUMER_SECRET"],
            )
        except KeyError as missing:
            raise WooError(f"Missing setting: {missing.args[0]}") from None

    def _signed_url(self, method, url, params):
        """Return the url with OAuth 1.0a (one-legged) signing added."""
        all_params = dict(params)
        all_params["oauth_consumer_key"] = self.consumer_key
        all_params["oauth_timestamp"] = str(int(time.time()))
        all_params["oauth_nonce"] = secrets.token_hex(8)
        all_params["oauth_signature_method"] = "HMAC-SHA256"

        # The signature covers the method, the url and the sorted parameters.
        pairs = sorted((quote(k, safe=""), quote(str(v), safe="")) for k, v in all_params.items())
        query = "&".join(f"{k}={v}" for k, v in pairs)
        base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(query, safe='')}"

        # One-legged OAuth has no token, so the signing key is "secret&".
        key = (self.consumer_secret + "&").encode()
        digest = hmac.new(key, base_string.encode(), hashlib.sha256).digest()
        signature = quote(base64.b64encode(digest).decode(), safe="")
        return f"{url}?{query}&oauth_signature={signature}"

    async def request(self, method, path, params=None, json=None):
        """Send one request to the store and return the decoded JSON."""
        url = self._signed_url(method, self.api_url + path, params or {})
        try:
            async with httpx2.AsyncClient(timeout=httpx2.Timeout(self.timeout)) as client:
                response = await client.request(method, url, json=json)
        except httpx2.TimeoutException as error:
            raise WooError("The store took too long to answer (timeout).") from error
        except httpx2.TransportError as error:
            raise WooError("Could not reach the store. Is it running?") from error

        if response.status_code >= 400:
            raise WooError(f"The store returned error {response.status_code}: {_error_text(response)}")
        return response.json()

    async def get(self, path, params=None):
        return await self.request("GET", path, params=params)

    async def post(self, path, body):
        return await self.request("POST", path, json=body)

    async def put(self, path, body):
        return await self.request("PUT", path, json=body)