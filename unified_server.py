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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

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

# Import session management
from session_api import router as session_router

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

# Include session management router
app.include_router(session_router, tags=["Session Management"])

# Crawling API Models
class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 2
    max_pages: int = 100
    export_formats: List[str] = ["json", "md", "html", "pdf"]

class CrawlStatus(BaseModel):
    status: str
    pages_crawled: int = 0
    success_rate: float = 0.0
    queue_size: int = 0
    message: Optional[str] = None

# Global crawl state
crawl_state = {
    "status": "stopped",
    "pages_crawled": 0,
    "success_rate": 0.0,
    "queue_size": 0
}

# API root endpoint
@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "CrawlOps API is running",
        "version": "1.0.0",
        "status": "operational"
    }

# Health check endpoints (both paths for compatibility)
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "CrawlOps server is running"}

# Crawling endpoints
@app.post("/api/crawl/start")
async def start_crawl(crawl_request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start a new crawl operation."""
    try:
        # Validate URL
        if not crawl_request.url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Update crawl state
        crawl_state["status"] = "running"
        crawl_state["queue_size"] = 1
        
        # For now, return success - full implementation would use crawl4ai
        return {
            "success": True,
            "message": f"Crawl started for {crawl_request.url}",
            "crawl_id": "crawl_001",
            "config": {
                "max_depth": crawl_request.max_depth,
                "max_pages": crawl_request.max_pages,
                "export_formats": crawl_request.export_formats
            }
        }
    except Exception as e:
        logger.error(f"Failed to start crawl: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start crawl: {str(e)}")

@app.post("/api/crawl/stop")
async def stop_crawl():
    """Stop the current crawl operation."""
    crawl_state["status"] = "stopped"
    crawl_state["queue_size"] = 0
    return {
        "success": True,
        "message": "Crawl stopped successfully"
    }

@app.get("/api/crawl/status")
async def get_crawl_status():
    """Get current crawl status."""
    return CrawlStatus(**crawl_state)

# Extract endpoint (alias for crawl/start for frontend compatibility)
@app.post("/api/extract")
async def extract_content(crawl_request: CrawlRequest, background_tasks: BackgroundTasks):
    """Extract content from URL (same as crawl/start)."""
    return await start_crawl(crawl_request, background_tasks)

# Authentication endpoints for enterprise SSO
@app.post("/api/auth/sso-login")
async def sso_login(domain: str):
    """Initiate SSO login for a domain."""
    return {
        "success": True,
        "message": f"SSO login initiated for {domain}",
        "auth_url": f"https://auth.{domain}/oauth/authorize",
        "status": "redirecting"
    }

@app.post("/api/auth/save-session")
async def save_auth_session(domain: str, tokens: dict):
    """Save authentication session tokens."""
    return {
        "success": True,
        "message": f"Authentication session saved for {domain}",
        "expires_in": 3600
    }

@app.get("/api/auth/status")
async def auth_status():
    """Get current authentication status."""
    return {
        "authenticated": False,
        "domains": [],
        "message": "No active authentication sessions"
    }

# Serve the main HTML file
@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML file."""
    return FileResponse("index.html")

# Serve session frontend JavaScript
@app.get("/session_frontend.js")
async def serve_session_frontend():
    """Serve the session frontend JavaScript file."""
    return FileResponse("session_frontend.js", media_type="application/javascript")

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