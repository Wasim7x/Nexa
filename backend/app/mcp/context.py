from typing import Optional
from pydantic import BaseModel, Field

class MCPCallContext(BaseModel):
    """Trusted context provided to MCP tools from the authenticated application workflow."""
    merchant_id: str
    customer_id: str
    customer_phone: str
    conversation_id: Optional[str] = None
    caller_role: str = "customer"  # 'customer', 'staff', 'admin'
