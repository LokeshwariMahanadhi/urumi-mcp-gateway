"""One-time setup for a fresh install. Safe to run again.

Creates the tables, the first admin, a demo member, and registers the upstream
servers. Prints the two API keys ONCE, only when it creates them.
Run it as a Kubernetes Job (the Helm chart does this) or by hand.
"""
import os

from gateway import accounts
from gateway.db import connect, create_tables


def ensure_user(email, name, role):
    with connect() as db:
        row = db.execute("SELECT id FROM users WHERE email = %s", (email,)).fetchone()
    if row:
        return row[0], False
    return accounts.create_user(email, name, role), True


def ensure_server(name, url):
    with connect() as db:
        db.execute(
            "INSERT INTO upstream_servers (name, url) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET url = EXCLUDED.url",
            (name, url),
        )


def main():
    create_tables()
    for email, name, role in (
        (os.environ.get("ADMIN_EMAIL", "admin@example.com"), "Admin", "admin"),
        (os.environ.get("MEMBER_EMAIL", "member@example.com"), "Member", "member"),
    ):
        user_id, created = ensure_user(email, name, role)
        if created:
            print(f"Created {role} {email}. Key (shown once): {accounts.create_key(user_id, 'first key')}")
        else:
            print(f"{role} {email} already exists.")
    for name, url in (
        ("woocommerce", os.environ["WOOCOMMERCE_MCP_URL"]),
        ("currency", os.environ["CURRENCY_MCP_URL"]),
        ("utilities", os.environ["UTILITIES_MCP_URL"]),
    ):
        ensure_server(name, url)
        print(f"Registered upstream {name}.")


if __name__ == "__main__":
    main()
