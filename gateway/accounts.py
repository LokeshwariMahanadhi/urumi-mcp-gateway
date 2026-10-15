"""Users and API keys. All the database work for accounts lives here."""
import sys

from gateway.db import connect
from gateway.keys import hash_key, key_prefix, make_key


def create_user(email, name, role):
    with connect() as connection:
        row = connection.execute(
            "INSERT INTO users (email, name, role) VALUES (%s, %s, %s) RETURNING id",
            (email, name, role),
        ).fetchone()
    return row[0]


def create_key(user_id, label=""):
    """Make a key for a user. Returns the real key, which can't be read again."""
    key = make_key()
    with connect() as connection:
        connection.execute(
            "INSERT INTO api_keys (user_id, label, key_prefix, key_hash) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, label, key_prefix(key), hash_key(key)),
        )
    return key


def find_user_by_key(key):
    """Return the user for a valid, not-revoked key. Otherwise None."""
    with connect() as connection:
        row = connection.execute(
            "SELECT u.id, u.name, u.email, u.role "
            "FROM api_keys k JOIN users u ON u.id = k.user_id "
            "WHERE k.key_hash = %s AND k.revoked_at IS NULL",
            (hash_key(key),),
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3]}


def revoke_key(key_id):
    with connect() as connection:
        connection.execute(
            "UPDATE api_keys SET revoked_at = now() "
            "WHERE id = %s AND revoked_at IS NULL",
            (key_id,),
        )
def get_user_by_id(user_id):
    """Find a user by number. Returns None if they no longer exist."""
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, email, role FROM users WHERE id = %s",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3]}
if __name__ == "__main__":
    # python -m gateway.accounts create-admin EMAIL "NAME"
    # python -m gateway.accounts new-key USER_ID
    # python -m gateway.accounts revoke KEY_ID
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == "create-admin":
        user_id = create_user(args[1], args[2], "admin")
        print("Admin created. Your API key (shown only once, copy it now):")
        print(create_key(user_id, "first key"))
    elif len(args) == 2 and args[0] == "new-key":
        print(create_key(int(args[1]), "replacement key"))
    elif len(args) == 2 and args[0] == "revoke":
        revoke_key(int(args[1]))
        print("Key revoked.")
    elif len(args) == 3 and args[0] == "create-member":
        print(create_user(args[1], args[2], "member"))
    else:
        print("Commands: create-admin EMAIL NAME | new-key USER_ID | revoke KEY_ID")