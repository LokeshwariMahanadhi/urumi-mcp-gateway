"""Making and hashing API keys. The database only ever sees the hash."""
import hashlib
import secrets

PREFIX_LENGTH = 12


def make_key():
    """A new random key. Shown to the person once, never stored."""
    return "urumi_" + secrets.token_urlsafe(32)


def hash_key(key):
    """One-way fingerprint of a key. This is what goes in the database."""
    return hashlib.sha256(key.encode()).hexdigest()


def key_prefix(key):
    """First few characters, so people can tell their keys apart."""
    return key[:PREFIX_LENGTH]