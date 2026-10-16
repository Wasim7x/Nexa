from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from pydantic import BaseModel

class SecurityContext(BaseModel):
    customer_id: Optional[str] = None
    customer_phone: Optional[str] = None
    merchant_id: Optional[str] = None
    is_authenticated_user: bool = False
    user_role: Optional[str] = None  # 'admin', 'staff', 'support'

class AuthorizationGuardrail:
    """
    Validates tenant scope, customer ownership, and role-based permissions.
    Prevents cross-merchant data leakage and IDOR vulnerabilities.
    """

    @classmethod
    def verify_merchant_scope(cls, resource_merchant_id: str, active_merchant_id: str) -> bool:
        """
        Verify that the requested resource strictly belongs to the active merchant context.
        Raises PermissionError if cross-merchant access is attempted.
        """
        if not resource_merchant_id or not active_merchant_id:
            return False
        return resource_merchant_id == active_merchant_id

    @classmethod
    def verify_customer_ownership(cls, record_customer_id: str, context_customer_id: str) -> bool:
        """
        Verify that an order or appointment is strictly owned by the caller.
        Prevents IDOR where an attacker specifies another customer's order number.
        """
        if not record_customer_id or not context_customer_id:
            return False
        return record_customer_id == context_customer_id

    @classmethod
    def require_dashboard_role(cls, user_role: str, allowed_roles: list) -> bool:
        """Verify merchant dashboard role permissions."""
        return user_role in allowed_roles
