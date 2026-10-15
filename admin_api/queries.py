"""Read-only database queries for the dashboard. Key hashes are never selected."""
from gateway.db import connect


def _rows_as_dicts(cursor):
    names = [column.name for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def list_users():
    with connect() as connection:
        cursor = connection.execute(
            "SELECT id, name, email, role, created_at FROM users ORDER BY id"
        )
        return _rows_as_dicts(cursor)


def list_keys():
    with connect() as connection:
        cursor = connection.execute(
            "SELECT k.id, k.user_id, u.name AS user_name, k.label, k.key_prefix, "
            "k.created_at, k.revoked_at "
            "FROM api_keys k JOIN users u ON u.id = k.user_id ORDER BY k.id"
        )
        return _rows_as_dicts(cursor)


def list_audit(limit=100):
    with connect() as connection:
        cursor = connection.execute(
            "SELECT id, created_at, user_name, upstream, tool, duration_ms, outcome "
            "FROM audit_log ORDER BY id DESC LIMIT %s",
            (limit,),
        )
        return _rows_as_dicts(cursor)