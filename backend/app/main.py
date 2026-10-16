import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.customers import router as customers_router
from backend.app.api.catalog import router as catalog_router
from backend.app.api.operations import router as operations_router
from backend.app.api.knowledge import router as knowledge_router
from backend.app.api.escalations import router as escalations_router
from backend.app.api.offers import router as offers_router
from backend.app.api.settings import router as settings_router
from backend.app.api.whatsapp import router as whatsapp_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Vera: Multi-Merchant WhatsApp AI Assistant with LangGraph, MCP, and Strict AI Guardrails",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(customers_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(escalations_router, prefix="/api")
app.include_router(offers_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(whatsapp_router, prefix="/api")

# Mount built React frontend if dist exists
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
assets_dir = os.path.join(dist_dir, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(dist_dir, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa_routes(full_path: str):
        if full_path.startswith("api") or full_path in ["health", "ready", "docs", "openapi.json"]:
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = os.path.join(dist_dir, full_path)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(dist_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
