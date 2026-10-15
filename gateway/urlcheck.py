"""Safety check for the address of an upstream server an admin wants to add."""
import ipaddress
import os
import socket
from urllib.parse import urlparse


class UrlRejected(Exception):
    """The address is not allowed. The message is safe to show to the admin."""


def allowed_hosts_from_env():
    """Hosts the operator has approved, even if they are on a private network."""
    raw = os.environ.get("ALLOWED_UPSTREAM_HOSTS", "")
    return {name.strip().lower() for name in raw.split(",") if name.strip()}


def _addresses_of(hostname, resolve):
    try:
        infos = resolve(hostname, None)
    except OSError:
        raise UrlRejected("That host name could not be found.")
    return {ipaddress.ip_address(info[4][0]) for info in infos}


def _is_public(address):
    if address.version == 6 and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.is_global and not address.is_multicast


def check_upstream_url(url, allowed_hosts=None, resolve=socket.getaddrinfo):
    """Raise UrlRejected if the address is not safe to call. Otherwise return quietly."""
    if allowed_hosts is None:
        allowed_hosts = allowed_hosts_from_env()

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UrlRejected("The address must start with http:// or https://.")
    if not parsed.hostname:
        raise UrlRejected("The address has no host name.")
    if parsed.username or parsed.password:
        raise UrlRejected("The address must not contain a user name or password.")
    try:
        parsed.port
    except ValueError:
        raise UrlRejected("The port number is not valid.")

    if parsed.hostname.lower() in allowed_hosts:
        return

    # Every address the name points to must be public. One private answer is enough to refuse.
    for address in _addresses_of(parsed.hostname, resolve):
        if not _is_public(address):
            raise UrlRejected("That address points to a private or internal network, which is not allowed.")