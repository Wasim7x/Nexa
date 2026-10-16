from fastapi import APIRouter, status, Response
from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal
from backend.app.core.config import settings

router = APIRouter(tags=["Health & Readiness"])

@router.get("/health")
async def health_check():
    """Liveness probe: verifies process is responsive."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@router.get("/ready")
async def readiness_check():
    """Readiness probe: verifies database and dependencies are responsive."""
    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    if not db_ok:
        return Response(
            content='{"status": "degraded", "database": "unreachable"}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )

    return {
        "status": "ready",
        "database": "connected",
        "ai_provider": settings.AI_PROVIDER
    }
