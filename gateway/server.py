"""The gateway: one MCP server that gives access to every upstream server."""
import uvicorn
from mcp import types
from mcp.server import Server

from gateway.auth import AuthMiddleware
from gateway.permissions import can_use_tool
from gateway.upstreams import GatewayError, call_tool_on, list_all_tools, prefixed_name


def get_user(ctx):
    """The person who sent this request. AuthMiddleware put them there."""
    request = ctx.request
    if request is None:
        return None
    return request.scope.get("urumi_user")


def role_of(user):
    return user["role"] if user else None


async def list_tools(ctx, params):
    """Answer 'what tools do you have?' with only the tools this person may use."""
    role = role_of(get_user(ctx))
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
    """Answer 'run this tool' if allowed, by sending the call to the right upstream server."""
    role = role_of(get_user(ctx))
    if not can_use_tool(role, params.name):
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="You do not have permission to use this tool.")],
            is_error=True,
        )
    try:
        result = await call_tool_on(params.name, params.arguments or {})
    except GatewayError as error:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=str(error))],
            is_error=True,
        )
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
    uvicorn.run(app, host="127.0.0.1", port=8200)