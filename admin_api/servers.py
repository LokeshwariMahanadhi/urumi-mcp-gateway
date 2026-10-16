"""Database work for the list of upstream servers the gateway talks to."""
from gateway.db import connect


def list_servers():
    """All servers. The credential itself is never returned, only whether one is set."""
    with connect() as connection:
        cursor = connection.execute(
            "SELECT id, name, url, enabled, created_at, (credential IS NOT NULL AND credential <> '') AS has_credential "
            "FROM upstream_servers ORDER BY id"
        )
        names = [column.name for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


def add_server(name, url, credential=None):
    with connect() as connection:
        row = connection.execute(
            "INSERT INTO upstream_servers (name, url, credential) VALUES (%s, %s, %s) RETURNING id",
            (name, url, credential or None),
        ).fetchone()
    return row[0]


def set_enabled(server_id, enabled):
    """Returns True if the server exists."""
    with connect() as connection:
        cursor = connection.execute(
            "UPDATE upstream_servers SET enabled = %s WHERE id = %s", (enabled, server_id)
        )
        return cursor.rowcount > 0


def delete_server(server_id):
    """Returns True if the server existed."""
    with connect() as connection:
        cursor = connection.execute("DELETE FROM upstream_servers WHERE id = %s", (server_id,))
        return cursor.rowcount > 0
