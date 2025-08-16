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
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Fix Windows event loop policy for aiodns compatibility and Playwright issues
if platform.system() == 'Windows':
    try:
        import asyncio
        if sys.version_info >= (3, 8):
            # Windows ProactorEventLoop doesn't support aiodns and has Playwright subprocess issues
            # Force SelectorEventLoop on Windows for better compatibility
            if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                logging.info("Set Windows SelectorEventLoop policy for compatibility")
            else:
                # Fallback for older Python versions
                logging.warning("WindowsSelectorEventLoopPolicy not available, using default policy")
    except Exception as e:
        logging.warning(f"Failed to set Windows event loop policy: {e}")
        
    # Global Playwright disable flag for Windows if subprocess issues persist  
    import os
    os.environ.setdefault('PLAYWRIGHT_DISABLE_SUBPROCESS', '1')
    os.environ.setdefault('CRAWL4AI_BROWSER_TYPE', 'http_only')
    os.environ.setdefault('DISABLE_BROWSER_AUTOMATION', '1')
    logging.info("Set Windows compatibility environment variables for Playwright issues")

# Add the API directory to the path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

# Import session management
from session_api import router as session_router

# Configure comprehensive logging system with Windows support
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)

# Ensure log directory permissions for Windows
try:
    # Test write permissions
    test_file = log_dir / ".test_permissions"
    test_file.touch()
    test_file.unlink()
    logger_init_msg = f"Log directory initialized: {log_dir.absolute()}"
except Exception as e:
    # Fallback to user directory on Windows if current directory not writable
    if platform.system() == 'Windows':
        log_dir = Path.home() / "CrawlOpsStudio" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    logger_init_msg = f"Log directory created with fallback: {log_dir.absolute()} (reason: {e})"

# Create detailed logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Console output
        logging.StreamHandler(),
        # Main application log
        logging.FileHandler(log_dir / "crawlops_server.log", encoding='utf-8'),
        # Detailed scraping log
        logging.FileHandler(log_dir / "scraping_detailed.log", encoding='utf-8')
    ]
)

# Create specialized loggers
logger = logging.getLogger(__name__)
scraping_logger = logging.getLogger('scraping')
api_logger = logging.getLogger('api')

# Configure scraping logger with separate file
scraping_handler = logging.FileHandler(log_dir / "scraping_activity.log", encoding='utf-8')
scraping_handler.setFormatter(logging.Formatter('%(asctime)s - SCRAPING - %(levelname)s - %(message)s'))
scraping_logger.addHandler(scraping_handler)
scraping_logger.setLevel(logging.DEBUG)
# Prevent duplicate console output for scraping logger
scraping_logger.propagate = False

# Configure API logger
api_handler = logging.FileHandler(log_dir / "api_requests.log", encoding='utf-8')
api_handler.setFormatter(logging.Formatter('%(asctime)s - API - %(levelname)s - %(message)s'))
api_logger.addHandler(api_handler)
api_logger.setLevel(logging.INFO)
# Prevent duplicate console output for API logger
api_logger.propagate = False

# Log initialization message
print(logger_init_msg)
logger.info(logger_init_msg)
logger.info(f"Platform: {platform.system()}")
logger.info(f"Python version: {sys.version}")
logger.info("Logging system initialized successfully")

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
    delay_seconds: float = 1.0  # Configurable delay between requests (0.1-30.0 seconds)
    
    # Enterprise scope control (AWS Bedrock style)
    scope: str = "default"  # default, host_only, subdomains
    # Rate limiting (URLs per host per minute)
    max_urls_per_host_per_minute: int = 60
    # URL filtering patterns (regex)
    include_patterns: List[str] = []
    exclude_patterns: List[str] = []
    # Robots.txt compliance
    respect_robots_txt: bool = True
    # Custom user agent suffix
    user_agent_suffix: str = "CrawlOps-Studio/1.0"
    # Authentication options
    auth_type: str = "none"  # none, bearer, basic, custom
    auth_token: str = ""     # Bearer token or custom header value
    auth_username: str = ""  # For basic auth
    auth_password: str = ""  # For basic auth
    custom_headers: dict = {} # Additional custom headers

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
async def crawl_single_page(url: str, crawl_request: CrawlRequest):
    """Extract content from a single page using browser automation or HTTP fallback."""
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler
        
        # Apply configurable delay
        if crawl_request.delay_seconds > 0:
            delay = max(0.1, min(30.0, crawl_request.delay_seconds))
            scraping_logger.debug(f"Applying {delay}s delay before crawling {url}")
            await asyncio.sleep(delay)
        
        # Build authentication headers for browser automation
        crawler_headers = {}
        if crawl_request.auth_type == "bearer" and crawl_request.auth_token:
            crawler_headers["Authorization"] = f"Bearer {crawl_request.auth_token}"
            scraping_logger.info(f"Using Bearer token authentication for browser automation: {url}")
        elif crawl_request.auth_type == "basic" and crawl_request.auth_username and crawl_request.auth_password:
            import base64
            credentials = base64.b64encode(f"{crawl_request.auth_username}:{crawl_request.auth_password}".encode()).decode()
            crawler_headers["Authorization"] = f"Basic {credentials}"
            scraping_logger.info(f"Using Basic authentication for browser automation: {url} (user: {crawl_request.auth_username})")
        elif crawl_request.auth_type == "custom" and crawl_request.auth_token:
            crawler_headers["Authorization"] = crawl_request.auth_token
            scraping_logger.info(f"Using custom authorization header for browser automation: {url}")
        
        # Add custom headers
        if crawl_request.custom_headers:
            crawler_headers.update(crawl_request.custom_headers)
            scraping_logger.info(f"Added {len(crawl_request.custom_headers)} custom headers for browser automation: {url}")

        # Check Windows compatibility first
        use_browser_automation = True
        if platform.system() == 'Windows' and os.environ.get('DISABLE_BROWSER_AUTOMATION', '0') == '1':
            use_browser_automation = False
            scraping_logger.info(f"Skipping browser automation for {url} due to Windows compatibility issues")
        
        # Try crawl4ai first with enhanced JavaScript and cookies (if enabled)
        if use_browser_automation:
            try:
                async with AsyncWebCrawler(
                    headless=False,
                    browser_type="chromium",
                    verbose=True,
                    always_by_pass_cache=True,
                    delay_before_return_html=max(0.1, min(30.0, crawl_request.delay_seconds)),
                    headers=crawler_headers if crawler_headers else None
                ) as crawler:
                    result = await crawler.arun(
                        url=url,
                        js_code="window.scrollTo(0, document.body.scrollHeight); await new Promise(resolve => setTimeout(resolve, 2000));",
                        wait_for="body",
                        process_iframes=True,
                        remove_overlay_elements=True,
                        simulate_user=True,
                        override_navigator=True
                    )
                    
                    if result and hasattr(result, 'success') and result.success:
                        extracted_text = getattr(result, 'cleaned_html', '') or getattr(result, 'markdown', '') or "No content extracted"
                        links = getattr(result, 'links', []) if hasattr(result, 'links') else []
                        metadata = getattr(result, 'metadata', {}) if hasattr(result, 'metadata') else {}
                        media = getattr(result, 'media', []) if hasattr(result, 'media') else []
                        status_code = getattr(result, 'status_code', 200) if hasattr(result, 'status_code') else 200
                        
                        return {
                            "success": True,
                            "title": metadata.get('title', 'No title') if metadata else 'No title',
                            "content": extracted_text,
                            "word_count": len(extracted_text.split()) if extracted_text else 0,
                            "links": links,
                            "images": media[:5] if media else [],
                            "status_code": status_code,
                            "method": "browser_automation"
                        }
                    else:
                        error_msg = getattr(result, 'error_message', 'Unknown error') if result else 'No result returned'
                        raise Exception(f"Browser automation failed: {error_msg}")
                        
            except Exception as browser_error:
                # Fallback to enhanced HTTP extraction
                scraping_logger.warning(f"Browser automation failed for {url}: {str(browser_error)}")
                scraping_logger.info(f"Falling back to HTTP extraction for {url}")
        else:
            scraping_logger.info(f"Falling back to HTTP extraction for {url}")
        
        # HTTP extraction fallback (this should always execute when browser automation is disabled or fails)
        import aiohttp
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse, urldefrag
        
        auth_headers = {}
        if crawl_request.auth_type == "bearer" and crawl_request.auth_token:
            auth_headers["Authorization"] = f"Bearer {crawl_request.auth_token}"
            scraping_logger.info(f"Using Bearer token authentication for {url}")
        elif crawl_request.auth_type == "basic" and crawl_request.auth_username and crawl_request.auth_password:
            import base64
            credentials = base64.b64encode(f"{crawl_request.auth_username}:{crawl_request.auth_password}".encode()).decode()
            auth_headers["Authorization"] = f"Basic {credentials}"
            scraping_logger.info(f"Using Basic authentication for {url} (user: {crawl_request.auth_username})")
        elif crawl_request.auth_type == "custom" and crawl_request.auth_token:
            auth_headers["Authorization"] = crawl_request.auth_token
            scraping_logger.info(f"Using custom authorization header for {url}")
        
        # Add custom headers if provided
        if crawl_request.custom_headers:
            auth_headers.update(crawl_request.custom_headers)
            scraping_logger.info(f"Added {len(crawl_request.custom_headers)} custom headers for {url}")

        # Enhanced browser headers
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
        
        # Merge authentication headers with browser headers
        final_headers = {**browser_headers, **auth_headers}
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10),
            cookie_jar=aiohttp.CookieJar()
        ) as session:
            async with session.get(url, headers=final_headers, allow_redirects=True) as response:
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                title_text = title_tag.get_text(strip=True) if title_tag else "No title"
                
                # Extract text content
                for script in soup(["script", "style"]):
                    script.decompose()
                text_content = soup.get_text(separator=' ', strip=True)
                text_content = ' '.join(text_content.split())
                
                # Extract links
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    clean_url = urldefrag(absolute_url)[0]  # Remove fragments
                    if clean_url and clean_url.startswith(('http://', 'https://')):
                        links.append(clean_url)
                
                # Extract images
                images = []
                for img in soup.find_all('img', src=True):
                    img_url = urljoin(url, img['src'])
                    images.append(img_url)
                
                return {
                    "success": True,
                    "title": title_text,
                    "content": text_content,
                    "word_count": len(text_content.split()) if text_content else 0,
                    "links": links[:50],  # Limit to first 50 links
                    "images": images[:10],  # Limit to first 10 images
                    "status_code": response.status,
                    "method": "http_extraction"
                }
                    
    except Exception as e:
        scraping_logger.error(f"Failed to crawl {url}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "word_count": 0,
            "links": [],
            "images": []
        }

def apply_scope_filter(url: str, seed_url: str, scope: str) -> bool:
    """Apply AWS Bedrock-style scope filtering to URLs."""
    from urllib.parse import urlparse
    
    url_parsed = urlparse(url)
    seed_parsed = urlparse(seed_url)
    
    if scope == "default":
        # Same host and same initial path
        return (url_parsed.netloc.lower() == seed_parsed.netloc.lower() and 
                url_parsed.path.startswith(seed_parsed.path))
    elif scope == "host_only":
        # Same host only
        return url_parsed.netloc.lower() == seed_parsed.netloc.lower()
    elif scope == "subdomains":
        # Same primary domain (including subdomains)
        seed_domain_parts = seed_parsed.netloc.lower().split('.')
        url_domain_parts = url_parsed.netloc.lower().split('.')
        
        # Get primary domain (last two parts for .com, .org, etc.)
        if len(seed_domain_parts) >= 2:
            seed_primary = '.'.join(seed_domain_parts[-2:])
            if len(url_domain_parts) >= 2:
                url_primary = '.'.join(url_domain_parts[-2:])
                return url_primary == seed_primary
    
    return False

def apply_url_filters(url: str, include_patterns: List[str], exclude_patterns: List[str]) -> bool:
    """Apply URL filtering patterns with AWS Bedrock-style precedence."""
    import re
    
    # If exclusion patterns match, exclude (exclusion takes precedence)
    for pattern in exclude_patterns:
        try:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        except re.error:
            continue  # Skip invalid regex patterns
    
    # If no inclusion patterns, include by default
    if not include_patterns:
        return True
    
    # Check inclusion patterns
    for pattern in include_patterns:
        try:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        except re.error:
            continue  # Skip invalid regex patterns
    
    return False

async def check_robots_txt(url: str, user_agent: str) -> bool:
    """Check robots.txt compliance (RFC 9309 standard)."""
    try:
        from urllib.parse import urljoin, urlparse
        import aiohttp
        
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    # Simple robots.txt parsing
                    lines = robots_content.split('\n')
                    user_agent_block = False
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('#') or not line:
                            continue
                        
                        if line.lower().startswith('user-agent:'):
                            agent = line.split(':', 1)[1].strip()
                            user_agent_block = (agent == '*' or agent.lower() in user_agent.lower())
                        
                        if user_agent_block and line.lower().startswith('disallow:'):
                            path = line.split(':', 1)[1].strip()
                            if path and (path == '/' or parsed_url.path.startswith(path)):
                                return False
                    
                    return True
        return True  # Allow if robots.txt not found or accessible
    except:
        return True  # Allow on any error

async def recursive_crawl(crawl_request: CrawlRequest):
    """Perform recursive crawling with enterprise-grade scope control and filtering."""
    from urllib.parse import urlparse, urljoin
    import re
    
    crawled_urls = set()
    crawl_queue = [(crawl_request.url, 0)]  # (url, depth)
    results = []
    pages_crawled = 0
    rate_limit_tracker = {}  # Track URLs per host per minute
    user_agent = f"Mozilla/5.0 (compatible; {crawl_request.user_agent_suffix})"
    
    scraping_logger.info(f"Starting enterprise recursive crawl from {crawl_request.url}")
    scraping_logger.info(f"Config: Depth={crawl_request.max_depth}, Pages={crawl_request.max_pages}, Scope={crawl_request.scope}, RateLimit={crawl_request.max_urls_per_host_per_minute}/min")
    
    while crawl_queue and pages_crawled < crawl_request.max_pages:
        current_url, current_depth = crawl_queue.pop(0)
        
        # Skip if already crawled or depth exceeded
        if current_url in crawled_urls or current_depth > crawl_request.max_depth:
            continue
        
        # Apply enterprise scope filtering
        if not apply_scope_filter(current_url, crawl_request.url, crawl_request.scope):
            scraping_logger.debug(f"Skipping {current_url} - outside scope ({crawl_request.scope})")
            continue
        
        # Apply URL filtering patterns
        if not apply_url_filters(current_url, crawl_request.include_patterns, crawl_request.exclude_patterns):
            scraping_logger.debug(f"Skipping {current_url} - filtered by URL patterns")
            continue
        
        # Check robots.txt compliance if enabled and not being ignored
        if not crawl_request.ignore_robots and crawl_request.respect_robots_txt:
            if not await check_robots_txt(current_url, user_agent):
                scraping_logger.info(f"Skipping {current_url} - blocked by robots.txt")
                continue
        elif crawl_request.ignore_robots:
            scraping_logger.info(f"Ignoring robots.txt for {current_url} (user override)")
        
        crawled_urls.add(current_url)
        pages_crawled += 1
        
        # Update crawl state
        crawl_state["pages_crawled"] = pages_crawled
        crawl_state["queue_size"] = len(crawl_queue)
        crawl_state["success_rate"] = len([r for r in results if r.get("success", False)]) / max(pages_crawled, 1)
        
        scraping_logger.info(f"Crawling [{pages_crawled}/{crawl_request.max_pages}] depth {current_depth}: {current_url}")
        
        # Crawl the current page
        page_result = await crawl_single_page(current_url, crawl_request)
        
        # Ensure page_result is a dictionary before assignment (fix NoneType error)
        if not page_result or not isinstance(page_result, dict):
            page_result = {
                "success": False,
                "error": "No result returned from crawl_single_page", 
                "url": current_url,
                "word_count": 0,
                "links": [],
                "images": []
            }
            
        page_result["url"] = current_url
        page_result["depth"] = current_depth
        page_result["crawl_order"] = pages_crawled
        results.append(page_result)
        
        # If successful and not at max depth, add links to queue
        if page_result.get("success", False) and current_depth < crawl_request.max_depth:
            links = page_result.get("links", [])
            added_links = 0
            for link in links:
                if added_links >= 20:  # Limit to 20 links per page to avoid explosion
                    break
                    
                if link not in crawled_urls and link not in [url for url, _ in crawl_queue]:
                    # Apply scope filter to new links
                    if apply_scope_filter(link, crawl_request.url, crawl_request.scope):
                        # Apply URL filtering
                        if apply_url_filters(link, crawl_request.include_patterns, crawl_request.exclude_patterns):
                            # Basic file type filtering (exclude binary files)
                            if not re.search(r'\.(pdf|zip|exe|dmg|doc|docx|xls|xlsx|ppt|pptx|jpg|jpeg|png|gif|mp4|avi|mov)$', link, re.I):
                                crawl_queue.append((link, current_depth + 1))
                                added_links += 1
                                scraping_logger.debug(f"Added to queue: {link} (depth {current_depth + 1})")
    
    return results

@app.post("/api/crawl/start")
async def start_crawl(crawl_request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start a new crawl operation with recursive crawling support."""
    api_logger.info(f"Crawl request received: {crawl_request.url}")
    scraping_logger.info(f"Starting crawl for {crawl_request.url} - Max Depth: {crawl_request.max_depth}, Max Pages: {crawl_request.max_pages}, Ignore Robots: {crawl_request.ignore_robots}")
    
    try:
        # Validate URL
        if not crawl_request.url.startswith(("http://", "https://")):
            api_logger.error(f"Invalid URL format: {crawl_request.url}")
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Update crawl state
        crawl_state["status"] = "running"
        crawl_state["pages_crawled"] = 0
        crawl_state["queue_size"] = 1
        crawl_state["success_rate"] = 0.0
        scraping_logger.debug(f"Crawl state updated: {crawl_state}")
        
        # Perform recursive crawling
        crawl_results = await recursive_crawl(crawl_request)
        
        # Process results - ensure proper success tracking
        successful_pages = [r for r in crawl_results if r.get("success", False)]
        failed_pages = [r for r in crawl_results if not r.get("success", False)]
        
        scraping_logger.info(f"Crawl results processed: {len(successful_pages)} successful, {len(failed_pages)} failed, {len(crawl_results)} total")
        
        total_words = sum(r.get("word_count", 0) for r in successful_pages)
        all_links = []
        all_images = []
        
        for result in successful_pages:
            all_links.extend(result.get("links", []))
            all_images.extend(result.get("images", []))
        
        # Remove duplicates while preserving order
        unique_links = list(dict.fromkeys(all_links))
        unique_images = list(dict.fromkeys(all_images))
        
        # Create combined content for export
        combined_content = ""
        combined_markdown = ""
        combined_html = "<html><head><title>Recursive Crawl Results</title></head><body>"
        
        for result in successful_pages:
            combined_content += f"\n\n=== {result.get('title', 'Untitled')} ({result.get('url', '')}) ===\n"
            combined_content += result.get("content", "")
            
            combined_markdown += f"\n\n# {result.get('title', 'Untitled')}\n"
            combined_markdown += f"**URL:** {result.get('url', '')}\n"
            combined_markdown += f"**Words:** {result.get('word_count', 0)}\n\n"
            combined_markdown += result.get("content", "")
            
            combined_html += f"<div style='margin: 20px 0; border-bottom: 1px solid #ccc; padding-bottom: 20px;'>"
            combined_html += f"<h2>{result.get('title', 'Untitled')}</h2>"
            combined_html += f"<p><strong>URL:</strong> <a href='{result.get('url', '')}'>{result.get('url', '')}</a></p>"
            combined_html += f"<p><strong>Words:</strong> {result.get('word_count', 0)}</p>"
            combined_html += f"<div>{result.get('content', '')}</div></div>"
        
        combined_html += "</body></html>"
        
        # Initialize variables for all cases
        crawl_data = {
            "crawl_summary": {
                "start_url": crawl_request.url,
                "total_pages": len(crawl_results),
                "successful_pages": len(successful_pages),
                "failed_pages": len(failed_pages),
                "total_words": total_words,
                "unique_links": len(unique_links),
                "unique_images": len(unique_images),
                "max_depth_reached": max(r.get("depth", 0) for r in crawl_results) if crawl_results else 0
            },
            "pages": crawl_results,
            "combined_content": combined_content,
            "timestamp": datetime.now().isoformat()
        }
        files_saved = []
        
        # Save to output folder if there are successful results
        if successful_pages:
            output_dir = Path("./crawl_output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = crawl_request.url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")[:30]
            
            # Save combined results
            import json as json_module
            
            json_file = output_dir / f"recursive_crawl_{base_name}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json_module.dump(crawl_data, f, indent=2, ensure_ascii=False)
            
            md_file = output_dir / f"recursive_crawl_{base_name}_{timestamp}.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(combined_markdown)
            
            html_file = output_dir / f"recursive_crawl_{base_name}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(combined_html)
            
            txt_file = output_dir / f"recursive_crawl_{base_name}_{timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            files_saved = [json_file.name, md_file.name, html_file.name, txt_file.name]
            scraping_logger.info(f"Recursive crawl completed: {len(successful_pages)} pages, {total_words} words, files saved: {files_saved}")
        
        # Update final crawl state
        crawl_state["status"] = "completed"
        crawl_state["pages_crawled"] = len(successful_pages)
        crawl_state["success_rate"] = len(successful_pages) / max(len(crawl_results), 1)
        crawl_state["queue_size"] = 0
        
        return {
            "success": True,
            "message": f"Recursive crawl completed: {len(successful_pages)} successful pages out of {len(crawl_results)} total",
            "crawl_id": f"crawl_{hash(crawl_request.url) % 10000}",
            "url": crawl_request.url,
            "meta": {
                "total_pages": len(crawl_results),
                "successful_pages": len(successful_pages),
                "failed_pages": len(failed_pages),
                "total_words": total_words,
                "unique_links": len(unique_links),
                "unique_images": len(unique_images),
                "max_depth_reached": max(r.get("depth", 0) for r in crawl_results) if crawl_results else 0,
                "output_folder": "crawl_output",
                "files_saved": files_saved if successful_pages else []
            },
            "json": crawl_data if crawl_data else {"error": "No successful pages crawled"},
            "markdown": combined_markdown,
            "html": combined_html,
            "text": combined_content,
            "pages": crawl_results,
            "config": {
                "max_depth": crawl_request.max_depth,
                "max_pages": crawl_request.max_pages,
                "export_formats": crawl_request.export_formats,
                "delay_seconds": crawl_request.delay_seconds
            }
        }
        
    except Exception as e:
        scraping_logger.error(f"RECURSIVE CRAWL FAILED for {crawl_request.url}: {str(e)}")
        api_logger.error(f"Crawl request failed: {crawl_request.url} - Error: {str(e)}")
        logger.error(f"Failed to start recursive crawl: {e}")
        
        # Update crawl state on failure
        crawl_state["status"] = "failed"
        crawl_state["queue_size"] = 0
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
    """Capture rich HTML with CSS, images, fonts, and JavaScript embedded for offline viewing."""
    try:
        import aiohttp
        from bs4 import BeautifulSoup
        import base64
        import re
        import mimetypes
        from urllib.parse import urljoin, urlparse
        from datetime import datetime
        
        start_time = datetime.now()
        resources_inlined = []
        
        # Enhanced headers to mimic real browser
        headers = {
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
        
        # Add authentication if provided
        auth_headers = {}
        if hasattr(crawl_request, 'auth_type') and crawl_request.auth_type:
            if crawl_request.auth_type == 'bearer' and hasattr(crawl_request, 'auth_token'):
                auth_headers['Authorization'] = f"Bearer {crawl_request.auth_token}"
            elif crawl_request.auth_type == 'basic' and hasattr(crawl_request, 'auth_username'):
                import base64
                credentials = f"{crawl_request.auth_username}:{crawl_request.auth_password or ''}"
                encoded = base64.b64encode(credentials.encode()).decode()
                auth_headers['Authorization'] = f"Basic {encoded}"
            elif crawl_request.auth_type == 'custom' and hasattr(crawl_request, 'auth_token'):
                auth_headers['Authorization'] = crawl_request.auth_token
        
        headers.update(auth_headers)
        
        # Add custom headers if provided
        if hasattr(crawl_request, 'custom_headers') and crawl_request.custom_headers:
            try:
                import json
                custom = json.loads(crawl_request.custom_headers)
                headers.update(custom)
            except:
                pass
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            # Get the main page with enhanced browser simulation
            async with session.get(crawl_request.url) as response:
                html_content = await response.text()
                base_url = str(response.url)
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Add SingleFile metadata
            meta_tag = soup.new_tag('meta', attrs={'name': 'singlefile-captured', 'content': start_time.isoformat()})
            if soup.head:
                soup.head.insert(0, meta_tag)
            
            # Inline CSS files (external stylesheets)
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href and not href.startswith('data:'):
                    css_url = urljoin(base_url, href)
                    try:
                        async with session.get(css_url) as css_response:
                            if css_response.status == 200:
                                css_content = await css_response.text()
                                
                                # Process @import statements in CSS
                                import_pattern = r'@import\s+url\(["\']?([^"\']+)["\']?\);?'
                                for match in re.finditer(import_pattern, css_content):
                                    import_url = urljoin(css_url, match.group(1))
                                    try:
                                        async with session.get(import_url) as import_response:
                                            if import_response.status == 200:
                                                import_css = await import_response.text()
                                                css_content = css_content.replace(match.group(0), import_css)
                                    except:
                                        pass
                                
                                # Process font URLs in CSS
                                font_pattern = r'url\(["\']?([^"\']+\.(?:woff2?|ttf|eot|otf))["\']?\)'
                                for match in re.finditer(font_pattern, css_content):
                                    font_url = urljoin(css_url, match.group(1))
                                    try:
                                        async with session.get(font_url) as font_response:
                                            if font_response.status == 200:
                                                font_data = await font_response.read()
                                                if len(font_data) < 200000:  # Inline fonts under 200KB
                                                    content_type = font_response.headers.get('content-type', 'font/woff2')
                                                    if not content_type.startswith('font/'):
                                                        # Guess font type from extension
                                                        if '.woff2' in font_url:
                                                            content_type = 'font/woff2'
                                                        elif '.woff' in font_url:
                                                            content_type = 'font/woff'
                                                        elif '.ttf' in font_url:
                                                            content_type = 'font/ttf'
                                                    
                                                    b64_font = base64.b64encode(font_data).decode()
                                                    data_url = f"data:{content_type};base64,{b64_font}"
                                                    css_content = css_content.replace(match.group(0), f'url({data_url})')
                                                    resources_inlined.append('font')
                                    except:
                                        pass
                                
                                # Process background images in CSS
                                bg_pattern = r'url\(["\']?([^"\']+\.(?:png|jpg|jpeg|gif|svg|webp))["\']?\)'
                                for match in re.finditer(bg_pattern, css_content):
                                    img_url = urljoin(css_url, match.group(1))
                                    try:
                                        async with session.get(img_url) as img_response:
                                            if img_response.status == 200:
                                                img_data = await img_response.read()
                                                if len(img_data) < 100000:  # Inline background images under 100KB
                                                    content_type = img_response.headers.get('content-type')
                                                    if not content_type:
                                                        content_type, _ = mimetypes.guess_type(img_url)
                                                    if content_type and content_type.startswith('image/'):
                                                        b64_img = base64.b64encode(img_data).decode()
                                                        data_url = f"data:{content_type};base64,{b64_img}"
                                                        css_content = css_content.replace(match.group(0), f'url({data_url})')
                                                        resources_inlined.append('bg-image')
                                    except:
                                        pass
                                
                                # Create style tag and replace link
                                style_tag = soup.new_tag('style', attrs={'data-singlefile-css': href})
                                style_tag.string = css_content
                                link.replace_with(style_tag)
                                resources_inlined.append('css')
                    except Exception as e:
                        logger.debug(f"Failed to inline CSS {css_url}: {e}")
            
            # Inline images (img tags)
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and not src.startswith('data:'):
                    img_url = urljoin(base_url, src)
                    try:
                        async with session.get(img_url) as img_response:
                            if img_response.status == 200:
                                img_data = await img_response.read()
                                if len(img_data) < 500000:  # Inline images under 500KB
                                    content_type = img_response.headers.get('content-type')
                                    if not content_type:
                                        content_type, _ = mimetypes.guess_type(img_url)
                                    if content_type and content_type.startswith('image/'):
                                        b64_data = base64.b64encode(img_data).decode()
                                        img['src'] = f"data:{content_type};base64,{b64_data}"
                                        resources_inlined.append('image')
                    except Exception as e:
                        logger.debug(f"Failed to inline image {img_url}: {e}")
            
            # Inline favicon
            for link in soup.find_all('link', rel=lambda x: x and 'icon' in x):
                href = link.get('href')
                if href and not href.startswith('data:'):
                    icon_url = urljoin(base_url, href)
                    try:
                        async with session.get(icon_url) as icon_response:
                            if icon_response.status == 200:
                                icon_data = await icon_response.read()
                                if len(icon_data) < 50000:  # Inline small favicons
                                    content_type = icon_response.headers.get('content-type', 'image/x-icon')
                                    b64_data = base64.b64encode(icon_data).decode()
                                    link['href'] = f"data:{content_type};base64,{b64_data}"
                                    resources_inlined.append('favicon')
                    except:
                        pass
            
            # Remove external script tags that might break offline viewing
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src and any(domain in src for domain in ['google-analytics', 'googletagmanager', 'facebook', 'twitter']):
                    script.decompose()
            
            # Add SingleFile signature comment
            capture_time = datetime.now()
            elapsed = (capture_time - start_time).total_seconds()
            
            signature = f"""
<!--
 Page saved with SingleFile 
 url: {crawl_request.url} 
 saved date: {capture_time.strftime('%Y-%m-%d %H:%M:%S')} 
 resources inlined: {len(resources_inlined)} ({', '.join(set(resources_inlined))})
 capture time: {elapsed:.2f}s
-->"""
            
            # Get the final HTML
            final_html = signature + str(soup)
            size_bytes = len(final_html.encode('utf-8'))
            
            return {
                "success": True,
                "html": final_html,
                "size_bytes": size_bytes,
                "resources_inlined": list(set(resources_inlined)),
                "capture_time": f"{elapsed:.2f}s",
                "resources_count": len(resources_inlined)
            }
            
    except Exception as e:
        logger.error(f"SingleFile capture failed: {e}")
        import traceback
        logger.error(f"SingleFile error traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "html": f"<html><body><h1>SingleFile Capture Error</h1><p>{str(e)}</p></body></html>",
            "size_bytes": 0,
            "resources_inlined": [],
            "capture_time": "0.00s"
        }

# PDF processing endpoints
@app.post("/api/pdf/extract")
async def extract_pdf_links(file: UploadFile):
    """Extract links from uploaded PDF file."""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        import pypdf
        from io import BytesIO
        
        pdf_content = await file.read()
        pdf_reader = pypdf.PdfReader(BytesIO(pdf_content))
        
        links = []
        for page_num, page in enumerate(pdf_reader.pages):
            if '/Annots' in page:
                for annot in page['/Annots']:
                    annot_obj = annot.get_object()
                    if annot_obj.get('/Subtype') == '/Link':
                        if '/A' in annot_obj:
                            action = annot_obj['/A']
                            if action.get('/S') == '/URI':
                                uri = action.get('/URI')
                                if uri:
                                    links.append({
                                        "url": str(uri),
                                        "page": page_num + 1
                                    })
        
        return {
            "success": True,
            "filename": file.filename,
            "total_pages": len(pdf_reader.pages),
            "links_found": len(links),
            "links": links
        }
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "filename": file.filename
        }

@app.post("/api/pdf/parse")
async def parse_local_pdf(
    file: UploadFile = File(...),
    export_formats: str = Form("json,md,html,txt"),
    extract_links: bool = Form(True),
    follow_links: bool = Form(False),
    max_pages_from_links: int = Form(5),
    depth: int = Form(1)
):
    """Parse local PDF file and extract content with optional link following."""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        api_logger.info(f"Local PDF parsing started: {file.filename}")
        scraping_logger.info(f"Processing local PDF: {file.filename}")
        
        # Save uploaded file temporarily
        import tempfile
        import shutil
        from io import BytesIO
        
        pdf_content = await file.read()
        
        # Extract PDF content and metadata
        pdf_data = await extract_pdf_content(pdf_content, file.filename)
        
        if not pdf_data["success"]:
            raise HTTPException(status_code=400, detail=pdf_data["error"])
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace('.pdf', '').replace(' ', '_').replace('/', '_')
        base_filename = f"pdf_parse_{safe_filename}_{timestamp}"
        
        # Process export formats
        formats_list = [f.strip() for f in export_formats.split(',')]
        
        # Create results structure compatible with web crawling
        results = {
            "success": True,
            "message": f"PDF parsing completed: {file.filename}",
            "crawl_id": f"pdf_{hash(file.filename + timestamp) % 10000}",
            "source": f"Local PDF: {file.filename}",
            "meta": {
                "total_pages": pdf_data["total_pages"],
                "successful_pages": 1,
                "failed_pages": 0,
                "total_words": pdf_data["word_count"],
                "unique_links": len(pdf_data["links"]),
                "unique_images": 0,
                "max_depth_reached": 0,
                "output_folder": "crawl_output",
                "files_saved": []
            },
            "json": {
                "crawl_summary": {
                    "start_source": f"Local PDF: {file.filename}",
                    "total_pages": 1,
                    "successful_pages": 1,
                    "failed_pages": 0,
                    "total_words": pdf_data["word_count"],
                    "unique_links": len(pdf_data["links"]),
                    "unique_images": 0,
                    "max_depth_reached": 0
                },
                "pages": [{
                    "success": True,
                    "title": pdf_data["title"] or file.filename,
                    "content": pdf_data["content"],
                    "word_count": pdf_data["word_count"],
                    "links": [link["url"] for link in pdf_data["links"]],
                    "images": [],
                    "source_type": "pdf",
                    "filename": file.filename,
                    "total_pdf_pages": pdf_data["total_pages"],
                    "depth": 0,
                    "crawl_order": 1
                }],
                "combined_content": f"\n\n=== {pdf_data['title'] or file.filename} ===\n{pdf_data['content']}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add markdown format
        if "md" in formats_list or "markdown" in formats_list:
            results["markdown"] = f"""
# {pdf_data['title'] or file.filename}
**Source:** Local PDF File  
**Pages:** {pdf_data['total_pages']}  
**Words:** {pdf_data['word_count']}  
**Links Found:** {len(pdf_data['links'])}

{pdf_data['content']}

## Links Found in PDF
{chr(10).join(f"- [{link['url']}]({link['url']}) (Page {link['page']})" for link in pdf_data['links'])}
"""
        
        # Add HTML format
        if "html" in formats_list:
            results["html"] = f"""<html><head><title>PDF Parse Results</title></head><body>
<div style='margin: 20px 0; border-bottom: 1px solid #ccc; padding-bottom: 20px;'>
<h2>{pdf_data['title'] or file.filename}</h2>
<p><strong>Source:</strong> Local PDF File</p>
<p><strong>Pages:</strong> {pdf_data['total_pages']}</p>
<p><strong>Words:</strong> {pdf_data['word_count']}</p>
<p><strong>Links Found:</strong> {len(pdf_data['links'])}</p>
<div>{pdf_data['content'].replace(chr(10), '<br>')}</div>
<h3>Links Found</h3>
<ul>{''.join(f"<li><a href='{link['url']}'>{link['url']}</a> (Page {link['page']})</li>" for link in pdf_data['links'])}</ul>
</div></body></html>"""
        
        # Add text format
        if "txt" in formats_list or "text" in formats_list:
            results["text"] = f"""
=== {pdf_data['title'] or file.filename} ===
Source: Local PDF File
Pages: {pdf_data['total_pages']}
Words: {pdf_data['word_count']}
Links Found: {len(pdf_data['links'])}

{pdf_data['content']}

Links Found:
{chr(10).join(f"- {link['url']} (Page {link['page']})" for link in pdf_data['links'])}
"""
        
        # Save files to crawl_output
        output_dir = Path("./crawl_output")
        output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        
        # Save JSON
        if "json" in formats_list:
            json_file = output_dir / f"{base_filename}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results["json"], f, indent=2, ensure_ascii=False)
            saved_files.append(json_file.name)
        
        # Save Markdown
        if "md" in formats_list or "markdown" in formats_list:
            md_file = output_dir / f"{base_filename}.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(results["markdown"])
            saved_files.append(md_file.name)
        
        # Save HTML
        if "html" in formats_list:
            html_file = output_dir / f"{base_filename}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(results["html"])
            saved_files.append(html_file.name)
        
        # Save Text
        if "txt" in formats_list or "text" in formats_list:
            txt_file = output_dir / f"{base_filename}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(results["text"])
            saved_files.append(txt_file.name)
        
        results["meta"]["files_saved"] = saved_files
        
        # If follow_links is enabled, crawl discovered links
        if follow_links and pdf_data["links"]:
            scraping_logger.info(f"Following {len(pdf_data['links'])} links from PDF...")
            
            # Create crawl request for discovered links
            additional_pages = []
            crawled_count = 0
            
            for link_info in pdf_data["links"][:max_pages_from_links]:
                if crawled_count >= max_pages_from_links:
                    break
                    
                try:
                    # Create a basic crawl request for the link
                    from urllib.parse import urlparse
                    link_url = link_info["url"]
                    
                    # Skip non-HTTP URLs
                    parsed = urlparse(link_url)
                    if not parsed.scheme.startswith('http'):
                        continue
                    
                    scraping_logger.info(f"Crawling link from PDF page {link_info['page']}: {link_url}")
                    
                    # Create a simple crawl request
                    simple_request = CrawlRequest(
                        url=link_url,
                        max_depth=0,  # Don't go deeper from PDF links
                        max_pages=1,
                        export_formats=["json"],
                        auth_type="none",
                        ignore_robots=True
                    )
                    
                    # Crawl the single page
                    page_result = await crawl_single_page(link_url, simple_request)
                    
                    if page_result and page_result.get("success"):
                        additional_pages.append({
                            "success": True,
                            "title": page_result.get("title", "Unknown"),
                            "content": page_result.get("content", ""),
                            "word_count": page_result.get("word_count", 0),
                            "links": page_result.get("links", []),
                            "images": page_result.get("images", []),
                            "source_type": "web_from_pdf",
                            "pdf_page": link_info["page"],
                            "url": link_url,
                            "depth": 1,
                            "crawl_order": crawled_count + 2
                        })
                        crawled_count += 1
                        
                except Exception as e:
                    scraping_logger.error(f"Failed to crawl PDF link {link_url}: {e}")
                    continue
            
            if additional_pages:
                # Update results with additional pages
                results["json"]["pages"].extend(additional_pages)
                results["json"]["crawl_summary"]["total_pages"] += len(additional_pages)
                results["json"]["crawl_summary"]["successful_pages"] += len(additional_pages)
                results["json"]["crawl_summary"]["total_words"] += sum(p.get("word_count", 0) for p in additional_pages)
                results["json"]["crawl_summary"]["max_depth_reached"] = 1
                
                results["meta"]["total_pages"] += len(additional_pages)
                results["meta"]["successful_pages"] += len(additional_pages)
                results["meta"]["total_words"] += sum(p.get("word_count", 0) for p in additional_pages)
                results["meta"]["max_depth_reached"] = 1
                
                # Update combined content
                for page in additional_pages:
                    results["json"]["combined_content"] += f"\n\n=== {page['title']} ({page['url']}) ===\n{page['content']}"
                
                # Re-save JSON with additional pages
                if "json" in formats_list:
                    json_file = output_dir / f"{base_filename}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(results["json"], f, indent=2, ensure_ascii=False)
                
                scraping_logger.info(f"Successfully crawled {len(additional_pages)} additional pages from PDF links")
        
        api_logger.info(f"PDF parsing completed: {file.filename}, {len(saved_files)} files saved")
        
        return results
        
    except Exception as e:
        api_logger.error(f"PDF parsing failed: {str(e)}")
        scraping_logger.error(f"PDF parsing error for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")

async def extract_pdf_content(pdf_content: bytes, filename: str) -> dict:
    """Extract text content, metadata, and links from PDF bytes."""
    try:
        import pypdf
        from io import BytesIO
        
        pdf_reader = pypdf.PdfReader(BytesIO(pdf_content))
        
        # Extract text content from all pages
        full_text = ""
        links = []
        
        for page_num, page in enumerate(pdf_reader.pages):
            # Extract text
            page_text = page.extract_text()
            if page_text:
                full_text += f"\n\nPage {page_num + 1}:\n{page_text.strip()}"
            
            # Extract links
            if '/Annots' in page:
                for annot in page['/Annots']:
                    try:
                        annot_obj = annot.get_object()
                        if annot_obj.get('/Subtype') == '/Link':
                            if '/A' in annot_obj:
                                action = annot_obj['/A']
                                if action.get('/S') == '/URI':
                                    uri = action.get('/URI')
                                    if uri:
                                        links.append({
                                            "url": str(uri),
                                            "page": page_num + 1
                                        })
                    except Exception as e:
                        # Skip malformed annotations
                        continue
        
        # Extract metadata
        metadata = pdf_reader.metadata or {}
        title = metadata.get('/Title', filename)
        if title:
            title = str(title).strip()
        
        # Clean up text
        full_text = full_text.strip()
        word_count = len(full_text.split()) if full_text else 0
        
        return {
            "success": True,
            "content": full_text,
            "title": title,
            "total_pages": len(pdf_reader.pages),
            "word_count": word_count,
            "links": links,
            "metadata": {
                "author": str(metadata.get('/Author', '')) if metadata.get('/Author') else '',
                "subject": str(metadata.get('/Subject', '')) if metadata.get('/Subject') else '',
                "creator": str(metadata.get('/Creator', '')) if metadata.get('/Creator') else '',
                "producer": str(metadata.get('/Producer', '')) if metadata.get('/Producer') else '',
                "creation_date": str(metadata.get('/CreationDate', '')) if metadata.get('/CreationDate') else '',
                "modification_date": str(metadata.get('/ModDate', '')) if metadata.get('/ModDate') else ''
            }
        }
        
    except Exception as e:
        # Fallback to pdfminer for problematic PDFs
        try:
            from pdfminer.high_level import extract_text
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTTextContainer
            
            full_text = extract_text(BytesIO(pdf_content))
            word_count = len(full_text.split()) if full_text else 0
            
            return {
                "success": True,
                "content": full_text.strip(),
                "title": filename,
                "total_pages": 1,  # pdfminer doesn't easily provide page count
                "word_count": word_count,
                "links": [],  # pdfminer doesn't easily extract links
                "metadata": {}
            }
            
        except Exception as fallback_error:
            return {
                "success": False,
                "error": f"PDF extraction failed with both pypdf and pdfminer: {str(e)}, {str(fallback_error)}",
                "content": "",
                "title": filename,
                "total_pages": 0,
                "word_count": 0,
                "links": [],
                "metadata": {}
            }

# SSO Authentication System
import sqlite3
import json as json_module
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Initialize session database
def init_session_db():
    """Initialize SQLite database for session storage."""
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            session_data TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize session database on startup
init_session_db()

class SSORequest(BaseModel):
    domain: str = ""
    url: str = ""

@app.post("/api/auth/sso-login")
async def sso_login(request: SSORequest):
    """Initiate SSO login process."""
    try:
        url = request.url or f"https://{request.domain}"
        if not url:
            raise HTTPException(status_code=400, detail="URL or domain required for SSO login")
        
        domain = urlparse(url).netloc or request.domain
        
        # In a real implementation, this would redirect to the SSO provider
        # For now, we'll simulate the process
        auth_data = {
            "domain": domain,
            "auth_url": f"https://{domain}/auth/login",
            "state": f"state_{hash(domain) % 10000}",
            "redirect_uri": f"http://localhost:5000/api/auth/callback",
            "login_type": "sso"
        }
        
        api_logger.info(f"SSO login initiated for domain: {domain}")
        
        return {
            "success": True,
            "auth_url": auth_data["auth_url"],
            "state": auth_data["state"],
            "message": f"SSO login initiated for {domain}",
            "instructions": "Complete login in the opened browser window. The session will be saved automatically."
        }
        
    except Exception as e:
        api_logger.error(f"SSO login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SSO login failed: {str(e)}")

@app.post("/api/auth/save-session")
async def save_auth_session(request: dict):
    """Save authentication session data."""
    try:
        domain = request.get("domain", "")
        session_data = request.get("session_data", {})
        expires_hours = request.get("expires_hours", 24)  # Default 24 hours
        
        if not domain or not session_data:
            raise HTTPException(status_code=400, detail="Domain and session_data required")
        
        # Calculate expiration
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        # Save to database
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        
        # Remove existing sessions for this domain
        cursor.execute('DELETE FROM sessions WHERE domain = ?', (domain,))
        
        # Insert new session
        cursor.execute('''
            INSERT INTO sessions (domain, session_data, expires_at) 
            VALUES (?, ?, ?)
        ''', (domain, json_module.dumps(session_data), expires_at))
        
        conn.commit()
        conn.close()
        
        api_logger.info(f"Session saved for domain: {domain}, expires: {expires_at}")
        
        return {
            "success": True,
            "message": f"Session saved for {domain}",
            "domain": domain,
            "expires": expires_at.isoformat(),
            "session_id": f"session_{hash(domain) % 10000}"
        }
        
    except Exception as e:
        api_logger.error(f"Save session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")

@app.get("/api/auth/status")
async def auth_status():
    """Get current authentication status."""
    try:
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        
        # Get active sessions (not expired)
        cursor.execute('''
            SELECT domain, session_data, expires_at, created_at 
            FROM sessions 
            WHERE expires_at > datetime('now') 
            ORDER BY created_at DESC
        ''')
        
        active_sessions = []
        for row in cursor.fetchall():
            domain, session_data, expires_at, created_at = row
            try:
                session_obj = json_module.loads(session_data)
                active_sessions.append({
                    "domain": domain,
                    "expires_at": expires_at,
                    "created_at": created_at,
                    "session_type": session_obj.get("type", "unknown"),
                    "user": session_obj.get("user", "anonymous")
                })
            except:
                continue
        
        conn.close()
        
        # Clean up expired sessions
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE expires_at <= datetime("now")')
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            api_logger.info(f"Cleaned up {deleted_count} expired sessions")
        
        return {
            "authenticated": len(active_sessions) > 0,
            "active_sessions": len(active_sessions),
            "domains": [s["domain"] for s in active_sessions],
            "sessions": active_sessions,
            "message": f"{len(active_sessions)} active authentication sessions" if active_sessions else "No active authentication sessions"
        }
        
    except Exception as e:
        api_logger.error(f"Auth status check failed: {str(e)}")
        return {
            "authenticated": False,
            "active_sessions": 0,
            "domains": [],
            "sessions": [],
            "error": str(e),
            "message": "Failed to check authentication status"
        }

@app.post("/api/auth/logout")
async def logout(request: dict):
    """Logout and remove session for a domain."""
    try:
        domain = request.get("domain")
        if not domain:
            # Logout from all domains
            conn = sqlite3.connect('sessions.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions')
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            api_logger.info(f"Logged out from all domains ({deleted_count} sessions removed)")
            return {
                "success": True,
                "message": f"Logged out from all domains ({deleted_count} sessions removed)"
            }
        else:
            # Logout from specific domain
            conn = sqlite3.connect('sessions.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE domain = ?', (domain,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                api_logger.info(f"Logged out from {domain}")
                return {
                    "success": True,
                    "message": f"Logged out from {domain}"
                }
            else:
                return {
                    "success": False,
                    "message": f"No active session found for {domain}"
                }
        
    except Exception as e:
        api_logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

def get_session_for_domain(domain: str) -> dict:
    """Get active session data for a domain."""
    try:
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_data FROM sessions 
            WHERE domain = ? AND expires_at > datetime('now')
            ORDER BY created_at DESC LIMIT 1
        ''', (domain,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json_module.loads(row[0])
        return {}
    except:
        return {}

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

# Run the server
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting unified CrawlOps server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )