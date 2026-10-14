"""A tiny utilities MCP server: the current time, and a ping to check it is alive."""
from datetime import datetime, timedelta, timezone

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer(name="utilities")


@mcp.tool()
def get_time(utc_offset_hours: float = 0.0) -> dict:
    """Get the current time. Give the hours away from UTC (India is 5.5)."""
    if utc_offset_hours < -12 or utc_offset_hours > 14:
        raise ToolError("The UTC offset must be between -12 and 14 hours.")
    zone = timezone(timedelta(hours=utc_offset_hours))
    now = datetime.now(zone)
    return {"time": now.isoformat(timespec="seconds"), "utc_offset_hours": utc_offset_hours}


@mcp.tool()
def ping() -> str:
    """Check that the utilities server is alive."""
    return "pong from utilities"


# Keep this at the very bottom: it starts the server.
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8103)