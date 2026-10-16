"""The gateway: one MCP server that gives access to every upstream server."""
import os
import time

import uvicorn
from mcp import types
from mcp.server import Server

from gateway.audit import record
from gateway.auth import AuthMiddleware
from gateway.permissions import can_use_tool
from gateway.upstreams import GatewayError, call_tool_on, list_all_tools, prefixed_name, refresh_upstreams


def get_user(ctx):
    """The person who sent this request. AuthMiddleware put them there."""
    request = ctx.request
    if request is None:
        return None
    return request.scope.get("urumi_user")


def role_of(user):
    return user["role"] if user else None


def milliseconds_since(started):
    return int((time.monotonic() - started) * 1000)


def error_result(message):
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=message)],
        is_error=True,
    )


async def list_tools(ctx, params):
    """Answer 'what tools do you have?' with only the tools this person may use."""
    role = role_of(get_user(ctx))
    await refresh_upstreams()
    allowed = []
    for upstream in await list_all_tools():
        for tool in upstream.tools:
            full_name = prefixed_name(upstream.name, tool.name)
            if not can_use_tool(role, full_name):
                continue
            allowed.append(
                types.Tool(
                    name=full_name,
                    description=tool.description,
                    input_schema=tool.input_schema,
                    output_schema=tool.output_schema,
                )
            )
    return types.ListToolsResult(tools=allowed)


async def call_tool(ctx, params):
    """Run the tool if this person may, and write one audit log row either way."""
    user = get_user(ctx)
    started = time.monotonic()

    if not can_use_tool(role_of(user), params.name):
        await record(user, params.name, milliseconds_since(started), "denied")
        return error_result("You do not have permission to use this tool.")

    await refresh_upstreams()
    try:
        result = await call_tool_on(params.name, params.arguments or {})
    except GatewayError as error:
        await record(user, params.name, milliseconds_since(started), "gateway_error")
        return error_result(str(error))

    outcome = "tool_error" if result.is_error else "success"
    await record(user, params.name, milliseconds_since(started), outcome)
    # Build a fresh result so nothing internal from the upstream server leaks through.
    return types.CallToolResult(
        content=result.content,
        structured_content=result.structured_content,
        is_error=result.is_error,
    )


mcp_gateway = Server(
    "urumi-gateway",
    on_list_tools=list_tools,
    on_call_tool=call_tool,
)

# The web app that serves the MCP endpoint at /mcp.
# AuthMiddleware checks the API key before anything reaches the gateway.
app = AuthMiddleware(mcp_gateway.streamable_http_app())
# Keep this at the very bottom: it starts the gateway.
if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("BIND_HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8200")))