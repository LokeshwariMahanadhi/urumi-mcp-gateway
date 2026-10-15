"""The gateway: one MCP server that gives access to every upstream server."""
import uvicorn
from mcp import types
from mcp.server import Server

from gateway.upstreams import GatewayError, call_tool_on, list_all_tools, prefixed_name


async def list_tools(ctx, params):
    """Answer 'what tools do you have?' by combining every reachable upstream server."""
    combined = []
    for upstream in await list_all_tools():
        for tool in upstream.tools:
            combined.append(
                types.Tool(
                    name=prefixed_name(upstream.name, tool.name),
                    description=tool.description,
                    input_schema=tool.input_schema,
                    output_schema=tool.output_schema,
                )
            )
    return types.ListToolsResult(tools=combined)


async def call_tool(ctx, params):
    """Answer 'run this tool' by sending the call to the right upstream server."""
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
# API-key checking will be added in front of it on Day 4.
app = mcp_gateway.streamable_http_app()

# Keep this at the very bottom: it starts the gateway.
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8200)