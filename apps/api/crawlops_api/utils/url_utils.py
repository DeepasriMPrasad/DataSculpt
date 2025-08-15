import re
import logging
from urllib.parse import urlparse, urljoin, urlunparse, quote, unquote
from typing import List, Set, Optional, Dict, Any
import tldextract

logger = logging.getLogger(__name__)

# Common URL patterns for validation
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

# File extensions that are typically not crawlable
EXCLUDED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico',
    '.mp3', '.wav', '.ogg', '.m4a', '.mp4', '.avi', '.mov', '.wmv',
    '.zip', '.rar', '.tar', '.gz', '.7z', '.exe', '.dmg', '.pkg',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.css', '.js', '.xml', '.json', '.rss', '.atom'
}

def is_valid_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted and accessible.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic format validation
    if not URL_PATTERN.match(url):
        return False
    
    try:
        parsed = urlparse(url)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Scheme must be http or https
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Check for common non-crawlable file extensions
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"URL validation error for {url}: {str(e)}")
        return False

def normalize_url(url: str) -> str:
    """
    Normalize a URL for consistent comparison and storage.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL string
    """
    if not url:
        return url
    
    try:
        parsed = urlparse(url)
        
        # Convert scheme to lowercase
        scheme = parsed.scheme.lower()
        
        # Convert domain to lowercase
        netloc = parsed.netloc.lower()
        
        # Remove default ports
        if ':80' in netloc and scheme == 'http':
            netloc = netloc.replace(':80', '')
        elif ':443' in netloc and scheme == 'https':
            netloc = netloc.replace(':443', '')
        
        # Normalize path
        path = parsed.path
        if not path:
            path = '/'
        
        # Remove fragment (anchor)
        fragment = ''
        
        # Sort query parameters for consistent ordering
        query = parsed.query
        if query:
            # Parse and sort query parameters
            from urllib.parse import parse_qs, urlencode
            parsed_query = parse_qs(query, keep_blank_values=True)
            sorted_params = sorted(parsed_query.items())
            query = urlencode(sorted_params, doseq=True)
        
        # Reconstruct URL
        normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
        
        return normalized
        
    except Exception as e:
        logger.warning(f"URL normalization error for {url}: {str(e)}")
        return url

def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from a URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain string or None if extraction fails
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None

def extract_base_domain(url: str) -> Optional[str]:
    """
    Extract the base domain (without subdomains) from a URL.
    
    Args:
        url: URL to extract base domain from
        
    Returns:
        Base domain string or None if extraction fails
    """
    try:
        extracted = tldextract.extract(url)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        return None
    except Exception:
        # Fallback to simple parsing
        try:
            domain = extract_domain(url)
            if domain:
                parts = domain.split('.')
                if len(parts) >= 2:
                    return '.'.join(parts[-2:])
            return domain
        except Exception:
            return None

def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if same domain, False otherwise
    """
    domain1 = extract_domain(url1)
    domain2 = extract_domain(url2)
    return domain1 is not None and domain1 == domain2

def resolve_relative_url(base_url: str, relative_url: str) -> str:
    """
    Resolve a relative URL against a base URL.
    
    Args:
        base_url: Base URL
        relative_url: Relative URL to resolve
        
    Returns:
        Absolute URL
    """
    try:
        return urljoin(base_url, relative_url)
    except Exception as e:
        logger.warning(f"Failed to resolve relative URL {relative_url} against {base_url}: {str(e)}")
        return relative_url

def filter_urls_by_domain(urls: List[str], allowed_domains: List[str]) -> List[str]:
    """
    Filter URLs to only include those from allowed domains.
    
    Args:
        urls: List of URLs to filter
        allowed_domains: List of allowed domains
        
    Returns:
        Filtered list of URLs
    """
    if not allowed_domains:
        return urls
    
    filtered_urls = []
    allowed_domains_lower = [domain.lower() for domain in allowed_domains]
    
    for url in urls:
        domain = extract_domain(url)
        if domain and any(
            domain == allowed_domain or domain.endswith(f'.{allowed_domain}')
            for allowed_domain in allowed_domains_lower
        ):
            filtered_urls.append(url)
    
    return filtered_urls

def filter_urls_by_path_patterns(urls: List[str], disallowed_patterns: List[str]) -> List[str]:
    """
    Filter URLs to exclude those matching disallowed path patterns.
    
    Args:
        urls: List of URLs to filter
        disallowed_patterns: List of regex patterns for disallowed paths
        
    Returns:
        Filtered list of URLs
    """
    if not disallowed_patterns:
        return urls
    
    filtered_urls = []
    compiled_patterns = []
    
    # Compile regex patterns
    for pattern in disallowed_patterns:
        try:
            compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
        except re.error as e:
            logger.warning(f"Invalid regex pattern {pattern}: {str(e)}")
    
    for url in urls:
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # Check if path matches any disallowed pattern
            if not any(pattern.search(path) for pattern in compiled_patterns):
                filtered_urls.append(url)
            else:
                logger.debug(f"URL {url} filtered out by path pattern")
                
        except Exception as e:
            logger.warning(f"Error processing URL {url}: {str(e)}")
    
    return filtered_urls

def deduplicate_urls(urls: List[str]) -> List[str]:
    """
    Remove duplicate URLs, preserving order.
    
    Args:
        urls: List of URLs that may contain duplicates
        
    Returns:
        List of unique URLs
    """
    seen = set()
    deduped = []
    
    for url in urls:
        normalized = normalize_url(url)
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(url)
    
    return deduped

def extract_links_from_html(html_content: str, base_url: str) -> List[str]:
    """
    Extract all links from HTML content.
    
    Args:
        html_content: HTML content to parse
        base_url: Base URL for resolving relative links
        
    Returns:
        List of absolute URLs found in the HTML
    """
    links = []
    
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all <a> tags with href attributes
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if href:
                absolute_url = resolve_relative_url(base_url, href)
                if is_valid_url(absolute_url):
                    links.append(absolute_url)
        
        # Also check for links in other elements
        for element in soup.find_all(['link', 'area'], href=True):
            href = element['href'].strip()
            if href:
                absolute_url = resolve_relative_url(base_url, href)
                if is_valid_url(absolute_url):
                    links.append(absolute_url)
                    
    except ImportError:
        # Fallback regex-based extraction if BeautifulSoup not available
        logger.warning("BeautifulSoup not available, using regex fallback for link extraction")
        
        href_pattern = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
        matches = href_pattern.findall(html_content)
        
        for match in matches:
            href = match.strip()
            if href:
                absolute_url = resolve_relative_url(base_url, href)
                if is_valid_url(absolute_url):
                    links.append(absolute_url)
    
    except Exception as e:
        logger.error(f"Failed to extract links from HTML: {str(e)}")
    
    return deduplicate_urls(links)

def get_robots_txt_url(url: str) -> str:
    """
    Get the robots.txt URL for a given URL.
    
    Args:
        url: URL to get robots.txt for
        
    Returns:
        robots.txt URL
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        return robots_url
    except Exception:
        return f"{url.rstrip('/')}/robots.txt"

def parse_sitemap_urls(sitemap_content: str, base_url: str) -> List[str]:
    """
    Parse URLs from XML sitemap content.
    
    Args:
        sitemap_content: XML sitemap content
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List of URLs found in sitemap
    """
    urls = []
    
    try:
        # Simple regex-based extraction for sitemap URLs
        url_pattern = re.compile(r'<loc[^>]*>([^<]+)</loc>', re.IGNORECASE)
        matches = url_pattern.findall(sitemap_content)
        
        for match in matches:
            url = match.strip()
            if url.startswith(('http://', 'https://')):
                if is_valid_url(url):
                    urls.append(url)
            else:
                absolute_url = resolve_relative_url(base_url, url)
                if is_valid_url(absolute_url):
                    urls.append(absolute_url)
    
    except Exception as e:
        logger.error(f"Failed to parse sitemap: {str(e)}")
    
    return urls

def build_url_slug(url: str, max_length: int = 100) -> str:
    """
    Create a filesystem-safe slug from a URL.
    
    Args:
        url: URL to create slug from
        max_length: Maximum length of the slug
        
    Returns:
        URL slug safe for filesystem use
    """
    try:
        parsed = urlparse(url)
        
        # Start with domain
        domain = parsed.netloc.replace('www.', '')
        
        # Add path parts
        path_parts = [part for part in parsed.path.split('/') if part]
        
        # Build slug
        slug_parts = [domain] + path_parts
        slug = '_'.join(slug_parts)
        
        # Clean up for filesystem
        slug = re.sub(r'[^\w\-_.]', '_', slug)
        slug = re.sub(r'_+', '_', slug)
        slug = slug.strip('_')
        
        # Truncate if too long
        if len(slug) > max_length:
            slug = slug[:max_length].rstrip('_')
        
        return slug or 'page'
        
    except Exception as e:
        logger.warning(f"Failed to create slug for {url}: {str(e)}")
        return 'page'
