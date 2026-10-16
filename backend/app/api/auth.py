from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, create_access_token
from backend.app.models.shared import MerchantUser, Merchant
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    merchant_id: str
    merchant_name: str
    merchant_slug: str
    user_name: str
    role: str

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate merchant user and return JWT."""
    stmt = (
        select(MerchantUser, Merchant)
        .join(Merchant, MerchantUser.merchant_id == Merchant.id)
        .where(MerchantUser.email == req.email, MerchantUser.is_active == True)
    )
    res = await db.execute(stmt)
    record = res.first()

    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user, merchant = record
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(
        subject=user.id,
        extra_claims={
            "merchant_id": merchant.id,
            "role": user.role,
            "email": user.email
        }
    )

    return TokenResponse(
        access_token=token,
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        merchant_slug=merchant.slug,
        user_name=user.full_name,
        role=user.role
    )

@router.get("/me")
async def get_me(current_user: MerchantUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return currently authenticated user and merchant details."""
    merch_stmt = select(Merchant).where(Merchant.id == current_user.merchant_id)
    merchant = (await db.execute(merch_stmt)).scalars().first()

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "merchant": {
            "id": merchant.id if merchant else "",
            "name": merchant.name if merchant else "",
            "slug": merchant.slug if merchant else "",
            "business_type": merchant.business_type if merchant else ""
        }
    }
