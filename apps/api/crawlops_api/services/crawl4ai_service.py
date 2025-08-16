import asyncio
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import aiohttp
import time

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking
except ImportError:
    # Fallback if crawl4ai is not available
    AsyncWebCrawler = None

from ..models.schemas import ExtractResponse, ExtractMeta

logger = logging.getLogger(__name__)

class Crawl4aiService:
    """Service for extracting web content using crawl4ai."""
    
    def __init__(self):
        self.crawler: Optional[AsyncWebCrawler] = None
        self._initialized = False
        
    async def _initialize(self):
        """Initialize the crawl4ai crawler with Windows compatibility."""
        if self._initialized:
            return
            
        try:
            if AsyncWebCrawler is None:
                raise ImportError("crawl4ai package not available")
            
            # Check for Windows Playwright subprocess issues
            import platform
            import os
            if platform.system() == 'Windows' and os.environ.get('DISABLE_BROWSER_AUTOMATION', '0') == '1':
                logger.warning("Browser automation disabled on Windows due to Playwright subprocess issues")
                raise ImportError("Browser automation disabled for Windows compatibility")
                
            self.crawler = AsyncWebCrawler(
                # Configure crawler options
                verbose=True,
                always_by_pass_cache=False,
                base_directory="./crawl_cache"
            )
            await self.crawler.astart()
            self._initialized = True
            logger.info("Crawl4ai service initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize crawl4ai, using HTTP fallback: {str(e)}")
            # Fall back to basic HTTP extraction
            self.crawler = None
            self._initialized = True
    
    async def is_ready(self) -> bool:
        """Check if the service is ready."""
        if not self._initialized:
            await self._initialize()
        return True
    
    async def extract_content(
        self,
        url: str,
        timeout: int = 30,
        user_agent: Optional[str] = None,
        wait_for: Optional[str] = None,
        css_selector: Optional[str] = None,
        word_count_threshold: int = 10
    ) -> ExtractResponse:
        """
        Extract content from a URL using crawl4ai or fallback method.
        
        Args:
            url: Target URL to crawl
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            wait_for: CSS selector to wait for before extracting
            css_selector: CSS selector to extract specific content
            word_count_threshold: Minimum word count for content
            
        Returns:
            ExtractResponse with JSON data, markdown, and metadata
        """
        await self._initialize()
        
        start_time = time.time()
        
        try:
            if self.crawler:
                # Use crawl4ai for extraction
                result = await self._extract_with_crawl4ai(
                    url, timeout, user_agent, wait_for, css_selector
                )
            else:
                # Fallback to basic HTTP extraction
                result = await self._extract_with_fallback(
                    url, timeout, user_agent
                )
            
            # Filter content by word count threshold
            if result.get('word_count', 0) < word_count_threshold:
                logger.warning(f"Content below word threshold for {url}: {result.get('word_count', 0)} words")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Build metadata
            meta = ExtractMeta(
                title=result.get('title', ''),
                description=result.get('description', ''),
                status=result.get('status_code', 200),
                content_type=result.get('content_type', 'text/html'),
                word_count=result.get('word_count', 0),
                processing_time=round(processing_time, 2),
                links_found=len(result.get('links', [])),
                images_found=len(result.get('images', []))
            )
            
            return ExtractResponse(
                url=url,
                json=result.get('structured_data', {}),
                markdown=result.get('markdown', ''),
                meta=meta
            )
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            raise
    
    async def _extract_with_crawl4ai(
        self,
        url: str,
        timeout: int,
        user_agent: Optional[str],
        wait_for: Optional[str],
        css_selector: Optional[str]
    ) -> Dict[str, Any]:
        """Extract content using crawl4ai."""
        try:
            # Configure extraction strategy
            extraction_strategy = None
            if css_selector:
                # Use CSS selector for targeted extraction
                extraction_strategy = RegexChunking(patterns=[css_selector])
            
            # Perform the crawl
            result = await self.crawler.arun(
                url=url,
                extraction_strategy=extraction_strategy,
                bypass_cache=True,
                js_code=f"await new Promise(resolve => setTimeout(resolve, 1000));" if wait_for else None,
                wait_for=wait_for,
                timeout=timeout,
                user_agent=user_agent or "CrawlOps Studio/1.0"
            )
            
            if not result.success:
                raise Exception(f"Crawl4ai extraction failed: {result.error_message}")
            
            # Extract structured data
            structured_data = {}
            if result.extracted_content:
                try:
                    import json
                    structured_data = json.loads(result.extracted_content)
                except (json.JSONDecodeError, TypeError):
                    structured_data = {"content": result.extracted_content}
            
            # Parse links and images
            links = []
            images = []
            
            if result.links:
                for link_data in result.links:
                    if isinstance(link_data, dict):
                        links.append({
                            'url': link_data.get('url', ''),
                            'text': link_data.get('text', ''),
                            'title': link_data.get('title', '')
                        })
            
            if result.media:
                for media_data in result.media:
                    if isinstance(media_data, dict) and media_data.get('type') == 'image':
                        images.append({
                            'url': media_data.get('src', ''),
                            'alt': media_data.get('alt', ''),
                            'title': media_data.get('title', '')
                        })
            
            return {
                'title': result.metadata.get('title', '') if result.metadata else '',
                'description': result.metadata.get('description', '') if result.metadata else '',
                'markdown': result.markdown or '',
                'structured_data': structured_data,
                'status_code': 200,
                'content_type': 'text/html',
                'word_count': len((result.markdown or '').split()) if result.markdown else 0,
                'links': links,
                'images': images
            }
            
        except Exception as e:
            logger.error(f"Crawl4ai extraction error: {str(e)}")
            raise
    
    async def _extract_with_fallback(
        self,
        url: str,
        timeout: int,
        user_agent: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback extraction using basic HTTP requests."""
        logger.info(f"Using fallback extraction for {url}")
        
        headers = {
            'User-Agent': user_agent or 'CrawlOps Studio/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, headers=headers) as response:
                if response.status >= 400:
                    if response.status == 401:
                        raise Exception("AUTH_REQUIRED: Authentication required")
                    elif response.status == 403:
                        raise Exception("AUTH_REQUIRED: Access forbidden")
                    elif response.status >= 500:
                        raise Exception(f"HTTP_ERROR: Server error {response.status}")
                    else:
                        raise Exception(f"HTTP_ERROR: Client error {response.status}")
                
                content = await response.text()
                content_type = response.headers.get('content-type', 'text/html')
                
                # Basic HTML parsing
                title, description, markdown = self._parse_html_content(content)
                
                return {
                    'title': title,
                    'description': description,
                    'markdown': markdown,
                    'structured_data': {
                        'content': markdown,
                        'url': url,
                        'status': response.status
                    },
                    'status_code': response.status,
                    'content_type': content_type,
                    'word_count': len(markdown.split()) if markdown else 0,
                    'links': [],
                    'images': []
                }
    
    def _parse_html_content(self, html_content: str) -> tuple[str, str, str]:
        """Basic HTML parsing to extract title, description, and text content."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ''
            
            # Extract meta description
            description = ''
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # Extract main content (remove script and style tags)
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup
            text_content = main_content.get_text() if main_content else ''
            
            # Clean up text content
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            markdown = '\n'.join(chunk for chunk in chunks if chunk)
            
            return title, description, markdown
            
        except ImportError:
            # Fallback without BeautifulSoup
            import re
            
            # Extract title with regex
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ''
            
            # Extract meta description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else ''
            
            # Remove HTML tags for basic text extraction
            text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return title, description, text
    
    async def cleanup(self):
        """Clean up resources."""
        if self.crawler and self._initialized:
            try:
                await self.crawler.aclose()
                logger.info("Crawl4ai service cleaned up")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
