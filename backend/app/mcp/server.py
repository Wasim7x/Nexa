import inspect
from typing import Dict, Any, List, Optional
from mcp.server.mcpserver import MCPServer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.mcp.context import MCPCallContext
from backend.app.mcp.tools import MCPBusinessTools

# Initialize official MCP Server
mcp_server = MCPServer(
    name="nexa-merchant-mcp",
    version="1.0.0",
    instructions="Nexa Multi-Merchant Business Tools for grocery, sweets, salon, and dental clinic."
)

# Registry mapping tool name -> method in MCPBusinessTools
TOOL_DISPATCH_TABLE = {
    "search_products": MCPBusinessTools.search_products,
    "check_inventory": MCPBusinessTools.check_inventory,
    "get_product_price": MCPBusinessTools.get_product_price,
    "get_active_offers": MCPBusinessTools.get_active_offers,
    "create_order": MCPBusinessTools.create_order,
    "get_order": MCPBusinessTools.get_order,
    "cancel_order": MCPBusinessTools.cancel_order,
    "list_services": MCPBusinessTools.list_services,
    "check_available_slots": MCPBusinessTools.check_available_slots,
    "book_appointment": MCPBusinessTools.book_appointment,
    "get_appointment": MCPBusinessTools.get_appointment,
    "update_appointment": MCPBusinessTools.update_appointment,
    "cancel_appointment": MCPBusinessTools.cancel_appointment,
    "get_customer_profile": MCPBusinessTools.get_customer_profile,
    "create_support_escalation": MCPBusinessTools.create_support_escalation,
}

# Merchant tool authorization matrix
# Controls which merchant can invoke which tools
MERCHANT_TOOL_AUTHORIZATION = {
    "grocery-store": [
        "search_products", "check_inventory", "get_product_price",
        "get_active_offers", "create_order", "get_order", "cancel_order",
        "get_customer_profile", "create_support_escalation"
    ],
    "sweets-shop": [
        "search_products", "check_inventory", "get_product_price",
        "get_active_offers", "create_order", "get_order", "cancel_order",
        "get_customer_profile", "create_support_escalation"
    ],
    "glow-salon": [
        "list_services", "check_available_slots", "book_appointment",
        "get_appointment", "update_appointment", "cancel_appointment",
        "get_customer_profile", "create_support_escalation"
    ],
    "dental-clinic": [
        "list_services", "check_available_slots", "book_appointment",
        "get_appointment", "cancel_appointment",
        "get_customer_profile", "create_support_escalation"
    ]
}

def get_authorized_tools_for_merchant(merchant_id: str) -> List[str]:
    """Return list of authorized tool names for a specific merchant."""
    return MERCHANT_TOOL_AUTHORIZATION.get(merchant_id, [])

async def execute_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    ctx: MCPCallContext,
    session: AsyncSession
) -> Dict[str, Any]:
    """
    Safely executes an MCP tool after verifying merchant tool authorization.
    """
    # 1. Verify that tool is authorized for this merchant
    authorized_tools = get_authorized_tools_for_merchant(ctx.merchant_id)
    if tool_name not in authorized_tools:
        return {
            "success": False,
            "error": f"Tool '{tool_name}' is unauthorized for merchant '{ctx.merchant_id}'"
        }

    handler = TOOL_DISPATCH_TABLE.get(tool_name)
    if not handler:
        return {"success": False, "error": f"Unknown tool '{tool_name}'"}

    try:
        # Call handler passing session and context
        res = await handler(session=session, ctx=ctx, **arguments)
        return {"success": True, "data": res}
    except PermissionError as pe:
        return {"success": False, "error": str(pe), "status": "permission_denied"}
    except Exception as ex:
        return {"success": False, "error": f"Tool execution failed: {str(ex)}"}
