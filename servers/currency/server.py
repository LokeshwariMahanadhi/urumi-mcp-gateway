"""A small currency MCP server. The rates are sample data, so no internet is needed."""
import os
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer(name="currency")

# Sample rates: how many units of each currency equal 1 US dollar.
# These are fixed demo numbers, not live market prices.
RATES_PER_USD = {
    "USD": 1.0,
    "INR": 83.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 150.0,
}


def check_currency(code: str) -> str:
    code = code.strip().upper()
    if code not in RATES_PER_USD:
        known = ", ".join(sorted(RATES_PER_USD))
        raise ToolError(f"Unknown currency '{code}'. Supported: {known}.")
    return code


@mcp.tool()
def list_rates() -> dict:
    """Show the sample exchange rates (units of each currency per 1 US dollar)."""
    return {"base": "USD", "rates": RATES_PER_USD, "note": "Sample data, not live prices."}


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount from one currency to another using the sample rates."""
    if amount < 0:
        raise ToolError("The amount cannot be negative.")
    source = check_currency(from_currency)
    target = check_currency(to_currency)
    in_usd = amount / RATES_PER_USD[source]
    result = in_usd * RATES_PER_USD[target]
    return {
        "amount": amount,
        "from": source,
        "to": target,
        "result": round(result, 2),
        "note": "Sample rates.",
    }


@mcp.tool()
def ping() -> str:
    """Check that the currency server is alive."""
    return "pong from currency"


# Keep this at the very bottom: it starts the server.
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=os.environ.get("BIND_HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8102")))