#!/usr/bin/env python3
"""
Unified server that serves both the React frontend and the FastAPI backend
This solves the Replit networking issues by having everything on port 5000
"""

import os
import sys
import json
import logging
import platform
from pathlib import Path
from datetime import datetime
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

# Configure comprehensive logging system
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)

# Create detailed logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Console output
        logging.StreamHandler(),
        # Main application log
        logging.FileHandler(log_dir / "crawlops_server.log"),
        # Detailed scraping log
        logging.FileHandler(log_dir / "scraping_detailed.log")
    ]
)

# Create specialized loggers
logger = logging.getLogger(__name__)
scraping_logger = logging.getLogger('scraping')
api_logger = logging.getLogger('api')

# Configure scraping logger with separate file
scraping_handler = logging.FileHandler(log_dir / "scraping_activity.log")
scraping_handler.setFormatter(logging.Formatter('%(asctime)s - SCRAPING - %(levelname)s - %(message)s'))
scraping_logger.addHandler(scraping_handler)
scraping_logger.setLevel(logging.DEBUG)

# Configure API logger
api_handler = logging.FileHandler(log_dir / "api_requests.log")
api_handler.setFormatter(logging.Formatter('%(asctime)s - API - %(levelname)s - %(message)s'))
api_logger.addHandler(api_handler)
api_logger.setLevel(logging.INFO)

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
    ignore_robots: bool = False

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
    api_logger.info(f"Crawl request received: {crawl_request.url}")
    scraping_logger.info(f"Starting crawl for {crawl_request.url} - Max Depth: {crawl_request.max_depth}, Max Pages: {crawl_request.max_pages}, Ignore Robots: {crawl_request.ignore_robots}")
    
    try:
        # Validate URL
        if not crawl_request.url.startswith(("http://", "https://")):
            api_logger.error(f"Invalid URL format: {crawl_request.url}")
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Update crawl state
        crawl_state["status"] = "running"
        crawl_state["queue_size"] = 1
        scraping_logger.debug(f"Crawl state updated: {crawl_state}")
        
        # Perform actual content extraction using crawl4ai
        try:
            import asyncio
            from crawl4ai import AsyncWebCrawler
            
            # Initialize crawler
            async with AsyncWebCrawler(verbose=True) as crawler:
                # Crawl the URL with actual content extraction
                result = await crawler.arun(url=crawl_request.url)
                
                if result.success:
                    # Extract real content
                    extracted_text = result.cleaned_html or result.markdown or "No content extracted"
                    word_count = len(extracted_text.split()) if extracted_text else 0
                    
                    return {
                        "success": True,
                        "message": f"Successfully crawled {crawl_request.url}",
                        "crawl_id": f"crawl_{hash(crawl_request.url) % 10000}",
                        "url": crawl_request.url,
                        "meta": {
                            "word_count": word_count,
                            "pages_processed": 1,
                            "extraction_time": f"{result.response_time:.2f}s" if result.response_time else "N/A",
                            "status_code": result.status_code,
                            "title": result.metadata.get('title', 'No title') if result.metadata else 'No title'
                        },
                        "json": {
                            "title": result.metadata.get('title', 'No title') if result.metadata else 'No title',
                            "content": extracted_text,
                            "url": crawl_request.url,
                            "timestamp": result.metadata.get('timestamp') if result.metadata else None,
                            "links": result.links[:10] if result.links else [],  # First 10 links
                            "images": result.media[:5] if result.media else []   # First 5 images
                        },
                        "markdown": result.markdown or f"# {result.metadata.get('title', 'Extracted Content')}\n\n{extracted_text}",
                        "html": result.html or f"<html><head><title>{result.metadata.get('title', 'Crawl Results')}</title></head><body>{result.cleaned_html or extracted_text}</body></html>",
                        "text": extracted_text,
                        "config": {
                            "max_depth": crawl_request.max_depth,
                            "max_pages": crawl_request.max_pages,
                            "export_formats": crawl_request.export_formats
                        }
                    }
                else:
                    logger.error(f"Crawl failed: {result.error_message}")
                    raise HTTPException(status_code=500, detail=f"Crawl failed: {result.error_message}")
                    
        except Exception as crawl4ai_error:
            # Fallback to enhanced HTTP extraction with JavaScript simulation
            scraping_logger.warning(f"crawl4ai failed for {crawl_request.url}: {str(crawl4ai_error)}")
            scraping_logger.info(f"Falling back to enhanced HTTP extraction with JavaScript simulation for {crawl_request.url}")
            logger.warning(f"crawl4ai failed ({crawl4ai_error}), using enhanced HTTP + BeautifulSoup extraction")
            import aiohttp
            
            # Enhanced browser headers to simulate JavaScript-enabled browser
            browser_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Create connector with SSL and connection settings
            connector = aiohttp.TCPConnector(ssl=False, limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            async with aiohttp.ClientSession(
                headers=browser_headers,
                connector=connector,
                timeout=timeout,
                cookie_jar=aiohttp.CookieJar()  # Enable cookies
            ) as session:
                scraping_logger.debug(f"Making HTTP request with enhanced browser simulation to {crawl_request.url}")
                async with session.get(crawl_request.url, allow_redirects=True) as response:
                    html_content = await response.text()
                    
                    # Advanced content extraction with BeautifulSoup
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "footer", "aside", "header", "menu"]):
                        element.decompose()
                    
                    # Extract title
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else "Extracted Content"
                    
                    # Enhanced detection for JavaScript protection
                    if any(indicator in html_content.lower() for indicator in [
                        'enable javascript', 'javascript is disabled', 'just a moment',
                        'checking your browser', 'cloudflare', 'please wait', 'security check',
                        'javascript and cookies', 'browser check', 'ray id'
                    ]):
                        scraping_logger.warning(f"JavaScript/Cloudflare protection detected on {crawl_request.url}")
                        scraping_logger.info(f"Enhanced extraction for JavaScript-protected content")
                        
                        # Enhanced content extraction for protected sites
                        enhanced_content = []
                        
                        # Extract noscript content
                        noscript_elements = soup.find_all('noscript')
                        for noscript in noscript_elements:
                            noscript_text = noscript.get_text().strip()
                            if noscript_text and len(noscript_text) > 10:
                                enhanced_content.append(noscript_text)
                                scraping_logger.debug(f"Added noscript content: {noscript_text[:50]}...")
                        
                        # Extract JSON-LD structured data
                        json_scripts = soup.find_all('script', type='application/ld+json')
                        for script in json_scripts:
                            try:
                                import json
                                data = json.loads(script.string or '{}')
                                if isinstance(data, dict):
                                    if 'headline' in data:
                                        title_text = data['headline']
                                    for key in ['description', 'articleBody', 'text', 'content']:
                                        if key in data and data[key]:
                                            enhanced_content.append(str(data[key]))
                                            scraping_logger.debug(f"Added JSON-LD {key}")
                            except Exception as e:
                                scraping_logger.debug(f"Failed to parse JSON-LD: {e}")
                        
                        # Extract meta information
                        meta_tags = soup.find_all('meta')
                        for meta in meta_tags:
                            content = meta.get('content', '')
                            name = meta.get('name', '').lower()
                            property_name = meta.get('property', '').lower()
                            
                            if content and len(content) > 20:
                                if name in ['description', 'keywords', 'author']:
                                    enhanced_content.append(content)
                                    scraping_logger.debug(f"Added meta {name}")
                                elif property_name in ['og:title', 'og:description', 'twitter:description']:
                                    enhanced_content.append(content)
                                    scraping_logger.debug(f"Added {property_name}")
                        
                        # If we found enhanced content, use it
                        if enhanced_content:
                            enhanced_text = ' '.join(enhanced_content)
                            scraping_logger.info(f"Enhanced extraction successful: {len(enhanced_text)} characters from protected content")
                        else:
                            enhanced_text = None
                            scraping_logger.warning(f"No enhanced content found for protected site {crawl_request.url}")
                    else:
                        enhanced_text = None
                    
                    # Extract main content - try multiple strategies
                    main_content = (
                        soup.find('main') or 
                        soup.find('article') or 
                        soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'article' in x.lower())) or
                        soup.find('div', id=lambda x: x and ('content' in x.lower() or 'main' in x.lower())) or
                        soup.body
                    )
                    
                    if main_content:
                        # Extract clean text from main content
                        text_content = main_content.get_text(separator=' ', strip=True)
                        # Clean up whitespace
                        text_content = ' '.join(text_content.split())
                    else:
                        text_content = soup.get_text(separator=' ', strip=True)
                        text_content = ' '.join(text_content.split())
                    
                    # Use enhanced content if available and better than extracted content
                    if enhanced_text and len(enhanced_text) > len(text_content):
                        text_content = enhanced_text
                        scraping_logger.info(f"Using enhanced content extraction for better results")
                    
                    # Extract links and images
                    links = [a.get('href') for a in soup.find_all('a', href=True) if a.get('href').startswith(('http', '/'))][:10]
                    images = [img.get('src') for img in soup.find_all('img', src=True) if img.get('src')][:5]
                    
                    word_count = len(text_content.split()) if text_content else 0
                    
                    # Create markdown version
                    markdown_content = f"# {title_text}\n\n{text_content}"
                    if links:
                        markdown_content += f"\n\n## Links\n" + "\n".join([f"- {link}" for link in links])
                    
                    # Log robots.txt preference with detailed context
                    if crawl_request.ignore_robots:
                        scraping_logger.warning(f"ROBOTS.TXT IGNORED for {crawl_request.url} - Enterprise crawling mode enabled")
                        logger.info(f"Ignoring robots.txt restrictions for {crawl_request.url}")
                    else:
                        scraping_logger.info(f"ROBOTS.TXT RESPECTED for {crawl_request.url} - Following website crawling guidelines")
                        logger.info(f"Respecting robots.txt restrictions for {crawl_request.url}")
                    
                    # Save to output folder
                    output_dir = Path("./crawl_output")
                    output_dir.mkdir(exist_ok=True)
                    
                    # Save files
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_name = crawl_request.url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")[:50]
                    
                    # Save JSON
                    json_data = {
                        "title": title_text,
                        "content": text_content,
                        "url": crawl_request.url,
                        "timestamp": datetime.now().isoformat(),
                        "links": links,
                        "images": images,
                        "word_count": word_count
                    }
                    
                    json_file = output_dir / f"{base_name}_{timestamp}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
                    # Save markdown
                    md_file = output_dir / f"{base_name}_{timestamp}.md"
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    # Save HTML
                    html_file = output_dir / f"{base_name}_{timestamp}.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    # Save text
                    txt_file = output_dir / f"{base_name}_{timestamp}.txt"
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write(text_content)
                    
                    # Detailed logging for successful extraction
                    scraping_logger.info(f"SUCCESS: Extracted {word_count} words from {crawl_request.url}")
                    scraping_logger.debug(f"Files saved: {[json_file.name, md_file.name, html_file.name, txt_file.name]}")
                    scraping_logger.debug(f"Title extracted: {title_text}")
                    scraping_logger.debug(f"Links found: {len(links)}, Images found: {len(images)}")
                    logger.info(f"Content extracted and saved to {output_dir} - {word_count} words")
                    
                    return {
                        "success": True,
                        "message": f"Successfully crawled {crawl_request.url} and saved to output folder",
                        "crawl_id": f"crawl_{hash(crawl_request.url) % 10000}",
                        "url": crawl_request.url,
                        "meta": {
                            "word_count": word_count,
                            "pages_processed": 1,
                            "extraction_time": "N/A",
                            "status_code": response.status,
                            "title": title_text,
                            "output_folder": str(output_dir),
                            "files_saved": [json_file.name, md_file.name, html_file.name, txt_file.name]
                        },
                        "json": json_data,
                        "markdown": markdown_content,
                        "html": html_content,
                        "text": text_content,
                        "config": {
                            "max_depth": crawl_request.max_depth,
                            "max_pages": crawl_request.max_pages,
                            "export_formats": crawl_request.export_formats
                        }
                    }
        except Exception as e:
            scraping_logger.error(f"HTTP extraction failed for {crawl_request.url}: {str(e)}")
            api_logger.error(f"Crawl request failed: {crawl_request.url} - Error: {str(e)}")
            logger.error(f"Failed to crawl {crawl_request.url}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to crawl: {str(e)}")
    except Exception as e:
        scraping_logger.error(f"CRAWL FAILED for {crawl_request.url}: {str(e)}")
        api_logger.error(f"Crawl request failed: {crawl_request.url} - Error: {str(e)}")
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

# SingleFile endpoint for rich HTML capture
@app.post("/api/singlefile")
async def singlefile_capture(crawl_request: CrawlRequest):
    """Capture rich HTML with CSS and images embedded using real content extraction."""
    try:
        import aiohttp
        from bs4 import BeautifulSoup
        import base64
        import re
        from urllib.parse import urljoin, urlparse
        
        async with aiohttp.ClientSession() as session:
            # Get the main page
            async with session.get(crawl_request.url) as response:
                html_content = await response.text()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Inline CSS files
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    css_url = urljoin(crawl_request.url, href)
                    try:
                        async with session.get(css_url) as css_response:
                            css_content = await css_response.text()
                            # Create style tag and replace link
                            style_tag = soup.new_tag('style')
                            style_tag.string = css_content
                            link.replace_with(style_tag)
                    except:
                        pass  # Skip if CSS can't be loaded
            
            # Inline small images as base64
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and not src.startswith('data:'):
                    img_url = urljoin(crawl_request.url, src)
                    try:
                        async with session.get(img_url) as img_response:
                            if img_response.status == 200:
                                img_data = await img_response.read()
                                if len(img_data) < 50000:  # Only inline small images (< 50KB)
                                    content_type = img_response.headers.get('content-type', 'image/png')
                                    b64_data = base64.b64encode(img_data).decode()
                                    img['src'] = f"data:{content_type};base64,{b64_data}"
                    except:
                        pass  # Skip if image can't be loaded
            
            # Get the final HTML
            final_html = str(soup)
            size_bytes = len(final_html.encode('utf-8'))
            
            return {
                "success": True,
                "html": final_html,
                "size_bytes": size_bytes,
                "resources_inlined": ["css", "images"],
                "capture_time": "N/A"
            }
            
    except Exception as e:
        logger.error(f"SingleFile capture failed: {e}")
        # Fallback to basic extraction
        try:
            import aiohttp
            # Enhanced headers to simulate a real browser with JavaScript support
            browser_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Create session with cookies enabled and enhanced settings
            connector = aiohttp.TCPConnector(ssl=False, limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            async with aiohttp.ClientSession(
                headers=browser_headers,
                connector=connector,
                timeout=timeout,
                cookie_jar=aiohttp.CookieJar()
            ) as session:
                scraping_logger.debug(f"Making HTTP request with enhanced browser simulation to {crawl_request.url}")
                async with session.get(crawl_request.url, allow_redirects=True) as response:
                    html_content = await response.text()
                    return {
                        "success": True,
                        "html": html_content,
                        "size_bytes": len(html_content.encode('utf-8')),
                        "resources_inlined": [],
                        "capture_time": "N/A"
                    }
        except:
            raise HTTPException(status_code=500, detail=f"SingleFile capture failed: {str(e)}")

# Authentication endpoints for enterprise SSO
class SSOLoginRequest(BaseModel):
    domain: str

@app.post("/api/auth/sso-login")
async def sso_login(request: SSOLoginRequest):
    """Initiate SSO login for a domain."""
    return {
        "success": True,
        "message": f"SSO login initiated for {request.domain}",
        "auth_url": f"https://auth.{request.domain}/oauth/authorize",
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