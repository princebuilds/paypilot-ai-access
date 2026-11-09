"""FastAPI application factory, static file mounting, and router integration."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import health

app = FastAPI(title="PayPilot AI ACCESS")

# Routers
app.include_router(health.router, prefix="/api")

# Static files mount
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
