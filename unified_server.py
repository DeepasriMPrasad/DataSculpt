#!/usr/bin/env python3
"""
Unified server that serves both the React frontend and the FastAPI backend
This solves the Replit networking issues by having everything on port 5000
"""

import os
import sys
import logging
import platform
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Fix Windows event loop policy for aiodns compatibility
if platform.system() == 'Windows':
    try:
        import asyncio
        if sys.version_info >= (3, 8):
            # Windows ProactorEventLoop doesn't support aiodns
            # Force SelectorEventLoop on Windows
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logging.info("Set Windows SelectorEventLoop policy for aiodns compatibility")
    except Exception as e:
        logging.warning(f"Failed to set Windows event loop policy: {e}")

# Add the API directory to the path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from apps.api.crawlops_api.routers import extract, health, report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CrawlOps Studio",
    description="Unified frontend and backend for CrawlOps Studio",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include API routers with /api prefix
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(extract.router, prefix="/api", tags=["extraction"])
app.include_router(report.router, prefix="/api/report", tags=["reporting"])

# API root endpoint
@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "CrawlOps API is running",
        "version": "1.0.0",
        "status": "operational"
    }

# Serve the main HTML file
@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML file."""
    return FileResponse("index.html")

# Serve static files (if any)
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting unified CrawlOps server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )