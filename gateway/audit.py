"""Writes one audit log row for every tool call."""
import asyncio

from gateway.db import connect


def write_entry(user, upstream, tool, duration_ms, outcome):
    with connect() as connection:
        connection.execute(
            "INSERT INTO audit_log (user_id, user_name, upstream, tool, duration_ms, outcome) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                user["id"] if user else None,
                user["name"] if user else "unknown",
                upstream,
                tool,
                duration_ms,
                outcome,
            ),
        )


async def record(user, full_tool_name, duration_ms, outcome):
    """Log one call. A logging problem must never break the call itself."""
    upstream, _, tool = full_tool_name.partition("_")
    try:
        await asyncio.to_thread(write_entry, user, upstream, tool, duration_ms, outcome)
    except Exception as error:
        print("Could not write the audit log:", type(error).__name__)