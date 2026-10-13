"""WooCommerce MCP server: lets an AI assistant work with our store."""
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .woo_client import WooClient, load_env_file

# When running on a laptop, read the settings from the project .env file.
# In Docker or Kubernetes the same settings arrive as environment variables.
env_file = Path(__file__).resolve().parents[2] / ".env"
if env_file.exists():
    load_env_file(env_file)

mcp = MCPServer(name="woocommerce")
store = WooClient.from_env()


def short_product(product):
    """Keep only the fields an AI assistant needs."""
    return {
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "stock_quantity": product["stock_quantity"],
        "status": product["status"],
    }


@mcp.tool()
async def list_products(search: str = "", limit: int = 10) -> list[dict]:
    """List products in the store. Optionally search by name.

    Returns each product's id, name, price, stock quantity and status.
    """
    limit = max(1, min(limit, 50))
    params = {"per_page": limit}
    if search:
        params["search"] = search
    products = await store.get("/products", params)
    return [short_product(product) for product in products]


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8101)