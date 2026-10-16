from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.shared import MerchantUser, Merchant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> MerchantUser:
    """Dependency: Validate JWT and return current merchant user."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    stmt = select(MerchantUser).where(MerchantUser.id == user_id, MerchantUser.is_active == True)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or inactive")

    return user

async def get_current_merchant(
    current_user: MerchantUser = Depends(get_current_user),
    x_merchant_id: Optional[str] = Header(None, alias="X-Merchant-ID"),
    db: AsyncSession = Depends(get_db)
) -> Merchant:
    """Dependency: Verify and return the authorized active merchant."""
    # A user can manage their own merchant or if admin manage requested merchant
    merchant_id = x_merchant_id or current_user.merchant_id

    stmt = select(Merchant).where(Merchant.id == merchant_id, Merchant.is_active == True)
    res = await db.execute(stmt)
    merchant = res.scalars().first()

    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    return merchant
