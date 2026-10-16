"""WooCommerce MCP server: lets an AI assistant work with our store."""
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .woo_client import WooClient, WooError, load_env_file

# When running on a laptop, read the settings from the project .env file.
# In Docker or Kubernetes the same settings arrive as environment variables.
env_file = Path(__file__).resolve().parents[2] / ".env"
if env_file.exists():
    load_env_file(env_file)

mcp = MCPServer(name="woocommerce")
store = WooClient.from_env()

ORDER_STATUSES = {
    "any", "pending", "processing", "on-hold",
    "completed", "cancelled", "refunded", "failed",
}


async def ask_store(method, path, params=None, body=None):
    """Call the store. Turn store errors into a ToolError the AI can read.

    The SDK shows a ToolError message to the AI. Any other exception is
    treated as a crash and its message is hidden.
    """
    try:
        return await store.request(method, path, params=params, json=body)
    except WooError as error:
        raise ToolError(str(error)) from error


def short_product(product):
    """Keep only the fields an AI assistant needs."""
    return {
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "stock_quantity": product["stock_quantity"],
        "status": product["status"],
    }


def short_order(order):
    """Keep what an assistant needs. Leave out emails and addresses on purpose."""
    billing = order["billing"]
    name = (billing["first_name"] + " " + billing["last_name"]).strip()
    return {
        "id": order["id"],
        "status": order["status"],
        "total": order["total"],
        "currency": order["currency"],
        "date_created": order["date_created"],
        "customer": name or "Guest",
        "items": [
            {"name": item["name"], "quantity": item["quantity"]}
            for item in order["line_items"]
        ],
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
    products = await ask_store("GET", "/products", params=params)
    return [short_product(product) for product in products]


@mcp.tool()
async def list_orders(status: str = "any", limit: int = 10) -> list[dict]:
    """List recent orders, newest first. Filter by status if you like.

    Status can be any, pending, processing, on-hold, completed, cancelled,
    refunded or failed. Returns id, status, total, customer name and items.
    """
    if status not in ORDER_STATUSES:
        raise ToolError(f"Unknown status '{status}'. Use one of: {sorted(ORDER_STATUSES)}")
    limit = max(1, min(limit, 50))
    orders = await ask_store("GET", "/orders", params={"status": status, "per_page": limit})
    return [short_order(order) for order in orders]


@mcp.tool()
async def get_order(order_id: int) -> dict:
    """Get one order by its id, with its status, total, customer name and items."""
    if order_id < 1:
        raise ToolError("order_id must be a positive number.")
    order = await ask_store("GET", f"/orders/{order_id}")
    return short_order(order)


# Keep this at the very bottom: the server starts here, so every tool
# above must already be defined.
WRITABLE_STATUSES = ORDER_STATUSES - {"any"}


@mcp.tool()
async def create_product(name: str, price: float, stock_quantity: int | None = None) -> dict:
    """Create a new simple product in the store and publish it.

    Give the product name and price (in the store's currency). Optionally give
    a starting stock quantity. Returns the new product's id, name, price and stock.
    """
    name = name.strip()
    if not name or len(name) > 200:
        raise ToolError("name must be between 1 and 200 characters.")
    if price <= 0:
        raise ToolError("price must be greater than zero.")
    if stock_quantity is not None and stock_quantity < 0:
        raise ToolError("stock_quantity cannot be negative.")

    body = {"name": name, "type": "simple", "status": "publish", "regular_price": f"{price:.2f}"}
    if stock_quantity is not None:
        body["manage_stock"] = True
        body["stock_quantity"] = stock_quantity
    product = await ask_store("POST", "/products", body=body)
    return short_product(product)


@mcp.tool()
async def update_order_status(order_id: int, status: str) -> dict:
    """Change an order's status, for example from processing to completed.

    Status can be pending, processing, on-hold, completed, cancelled,
    refunded or failed. Returns the updated order.
    """
    if order_id < 1:
        raise ToolError("order_id must be a positive number.")
    if status not in WRITABLE_STATUSES:
        raise ToolError(f"Unknown status '{status}'. Use one of: {sorted(WRITABLE_STATUSES)}")
    order = await ask_store("PUT", f"/orders/{order_id}", body={"status": status})
    return short_order(order)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=os.environ.get("BIND_HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8101")))