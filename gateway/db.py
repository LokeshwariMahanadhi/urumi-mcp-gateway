"""Database helpers for the gateway. Uses PostgreSQL through psycopg."""
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def load_env_file(path):
    """Read NAME=value lines from a .env file. Real environment settings win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


load_env_file(ROOT / ".env")


def connect():
    """Open a connection to the gateway database."""
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("Missing setting: POSTGRES_PASSWORD")
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.environ.get("POSTGRES_PORT", "5433")),
        dbname=os.environ.get("POSTGRES_DB", "gateway"),
        user=os.environ.get("POSTGRES_USER", "gateway"),
        password=password,
    )


def create_tables():
    """Create the tables if they are not there yet. Safe to run again."""
    with connect() as connection:
        connection.execute(SCHEMA_FILE.read_text())


def list_tables():
    with connect() as connection:
        rows = connection.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ).fetchall()
    return [row[0] for row in rows]


if __name__ == "__main__":
    create_tables()
    print("Tables:", ", ".join(list_tables()))