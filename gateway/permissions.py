"""Which tools each role is allowed to see and call."""

# Tools that change the store. Only admins may use these.
ADMIN_ONLY_TOOLS = {
    "woocommerce_create_product",
    "woocommerce_update_order_status",
}


def can_use_tool(role, full_tool_name):
    """True if someone with this role may use the tool (full name, like woocommerce_list_orders)."""
    if role == "admin":
        return True
    if role == "member":
        return full_tool_name not in ADMIN_ONLY_TOOLS
    # A role we do not know about gets nothing.
    return False