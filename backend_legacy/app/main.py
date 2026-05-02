from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, products, collections, cart, checkout

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all tables on startup (optional if DB is down)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    logger.warning("Starting without database. API functionality may be limited.")

app = FastAPI(
    title="Ecommerce API",
    description="FastAPI backend for the Next.js ecommerce storefront",
    version="1.0.0",
)

# CORS — allow the Next.js frontend
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Register routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(collections.router)
app.include_router(cart.router)
app.include_router(checkout.router)

# Mount static files (after API routes)
frontend_path = os.path.join(os.getcwd(), "..", "dist")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="static")

@app.get("/api/health")
def health():
    return {"status": "healthy"}

# Catch-all route for SPA
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # If the path starts with api/, it means it didn't match any router (404)
    if full_path.startswith("api/"):
        return {"error": "Not Found"}, 404

    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"status": "ok", "message": "API is running. Frontend build not found."}
