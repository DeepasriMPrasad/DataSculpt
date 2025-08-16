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
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile
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

        # Try crawl4ai first with enhanced JavaScript and cookies
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
                
                if result.success:
                    extracted_text = result.cleaned_html or result.markdown or "No content extracted"
                    links = result.links if result.links else []
                    return {
                        "success": True,
                        "title": result.metadata.get('title', 'No title') if result.metadata else 'No title',
                        "content": extracted_text,
                        "word_count": len(extracted_text.split()) if extracted_text else 0,
                        "links": links,
                        "images": result.media[:5] if result.media else [],
                        "status_code": result.status_code,
                        "method": "browser_automation"
                    }
                else:
                    raise Exception(f"Browser automation failed: {result.error_message}")
                    
        except Exception as browser_error:
            # Fallback to enhanced HTTP extraction
            scraping_logger.warning(f"Browser automation failed for {url}: {str(browser_error)}")
            scraping_logger.info(f"Falling back to HTTP extraction for {url}")
            
            import aiohttp
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin, urlparse, urldefrag
            
            # Build authentication headers
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
            "url": url
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
        
        # Process results
        successful_pages = [r for r in crawl_results if r.get("success", False)]
        failed_pages = [r for r in crawl_results if not r.get("success", False)]
        
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
        
        # Save to output folder if there are successful results
        if successful_pages:
            output_dir = Path("./crawl_output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = crawl_request.url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")[:30]
            
            # Save combined results
            import json as json_module
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
            "json": crawl_data if successful_pages else {"error": "No successful pages crawled"},
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
        return {
            "success": False,
            "error": str(e),
            "html": f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>",
            "size_bytes": 0,
            "resources_inlined": [],
            "capture_time": "N/A"
        }

# PDF processing endpoint
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