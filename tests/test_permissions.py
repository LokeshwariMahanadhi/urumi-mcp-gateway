from gateway.permissions import can_use_tool


def test_admin_can_use_write_tools():
    assert can_use_tool("admin", "woocommerce_create_product")
    assert can_use_tool("admin", "woocommerce_update_order_status")


def test_member_cannot_use_write_tools():
    assert not can_use_tool("member", "woocommerce_create_product")
    assert not can_use_tool("member", "woocommerce_update_order_status")


def test_member_can_read_orders_and_use_other_servers():
    assert can_use_tool("member", "woocommerce_list_orders")
    assert can_use_tool("member", "currency_convert_currency")


def test_unknown_role_gets_nothing():
    assert not can_use_tool("hacker", "currency_ping")
    assert not can_use_tool(None, "currency_ping")