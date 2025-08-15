import logging
from pathlib import Path
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
import re

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:
    try:
        # Fallback to PyPDF2
        from PyPDF2 import PdfReader
        from PyPDF2.errors import PdfReadError
    except ImportError:
        PdfReader = None
        PdfReadError = Exception

try:
    import pdfminer.six
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.converter import TextConverter
    from io import StringIO
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

from ..models.schemas import PDFLinksResponse
from ..utils.url_utils import is_valid_url, normalize_url

logger = logging.getLogger(__name__)

class PDFLinkExtractor:
    """Service for extracting URLs from PDF files."""
    
    def __init__(self):
        self.url_patterns = [
            # HTTP/HTTPS URLs
            re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE),
            # FTP URLs  
            re.compile(r'ftp://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE),
            # Email addresses (will be converted to mailto:)
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            # Domain names (basic heuristic)
            re.compile(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b', re.IGNORECASE)
        ]
    
    async def extract_links(
        self, 
        pdf_path: str,
        base_url: Optional[str] = None,
        extract_from_text: bool = True,
        extract_from_annotations: bool = True
    ) -> PDFLinksResponse:
        """
        Extract URLs from a PDF file using multiple methods.
        
        Args:
            pdf_path: Path to the PDF file
            base_url: Base URL for resolving relative links
            extract_from_text: Whether to extract URLs from text content
            extract_from_annotations: Whether to extract URLs from PDF annotations
            
        Returns:
            PDFLinksResponse with extracted URLs and metadata
        """
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_file.is_file():
            raise ValueError(f"Path is not a file: {pdf_path}")
        
        logger.info(f"Extracting links from PDF: {pdf_path}")
        
        urls = set()
        extraction_methods = []
        
        try:
            # Method 1: Extract from PDF annotations (hyperlinks)
            if extract_from_annotations:
                annotation_urls = await self._extract_from_annotations(pdf_path)
                urls.update(annotation_urls)
                if annotation_urls:
                    extraction_methods.append("annotations")
                    logger.info(f"Found {len(annotation_urls)} URLs from annotations")
            
            # Method 2: Extract URLs from text content
            if extract_from_text:
                text_urls = await self._extract_from_text(pdf_path)
                urls.update(text_urls)
                if text_urls:
                    extraction_methods.append("text_extraction")
                    logger.info(f"Found {len(text_urls)} URLs from text content")
            
            # Normalize and validate URLs
            valid_urls = []
            for url in urls:
                try:
                    # Convert email to mailto
                    if '@' in url and not url.startswith(('http', 'ftp', 'mailto')):
                        url = f"mailto:{url}"
                    
                    # Add protocol if missing for domain names
                    elif '.' in url and not url.startswith(('http', 'ftp', 'mailto')):
                        # Basic heuristic: if it looks like a domain, add https://
                        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.-]+[a-zA-Z0-9]\.[a-zA-Z]{2,}$', url):
                            url = f"https://{url}"
                    
                    # Resolve relative URLs
                    if base_url and not url.startswith(('http', 'ftp', 'mailto')):
                        url = urljoin(base_url, url)
                    
                    # Validate and normalize
                    if is_valid_url(url):
                        normalized_url = normalize_url(url)
                        if normalized_url not in [u['url'] for u in valid_urls]:
                            valid_urls.append({
                                'url': normalized_url,
                                'original': url,
                                'source': 'pdf_extraction'
                            })
                
                except Exception as e:
                    logger.warning(f"Failed to process URL {url}: {str(e)}")
                    continue
            
            # Sort URLs alphabetically
            valid_urls.sort(key=lambda x: x['url'])
            
            logger.info(f"Successfully extracted {len(valid_urls)} valid URLs from PDF")
            
            return PDFLinksResponse(
                url_count=len(valid_urls),
                urls=[url_data['url'] for url_data in valid_urls],
                extraction_methods=extraction_methods,
                file_info={
                    'path': pdf_path,
                    'size': pdf_file.stat().st_size,
                    'name': pdf_file.name
                }
            )
            
        except Exception as e:
            logger.error(f"PDF link extraction failed for {pdf_path}: {str(e)}")
            raise Exception(f"Failed to extract links from PDF: {str(e)}")
    
    async def _extract_from_annotations(self, pdf_path: str) -> Set[str]:
        """Extract URLs from PDF annotations (hyperlinks)."""
        urls = set()
        
        if PdfReader is None:
            logger.warning("PyPDF2/pypdf not available, skipping annotation extraction")
            return urls
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        if '/Annots' in page:
                            annotations = page['/Annots']
                            
                            for annotation_ref in annotations:
                                annotation = annotation_ref.get_object()
                                
                                # Look for URI annotations (hyperlinks)
                                if annotation.get('/Subtype') == '/Link':
                                    if '/A' in annotation:
                                        action = annotation['/A']
                                        if action.get('/S') == '/URI':
                                            uri = action.get('/URI')
                                            if uri:
                                                urls.add(str(uri))
                                
                                # Look for GoToR actions (external file links)
                                elif annotation.get('/Subtype') == '/GoToR':
                                    if '/F' in annotation:
                                        file_spec = annotation['/F']
                                        if isinstance(file_spec, str):
                                            urls.add(file_spec)
                    
                    except Exception as e:
                        logger.warning(f"Error processing page {page_num + 1}: {str(e)}")
                        continue
        
        except (PdfReadError, Exception) as e:
            logger.warning(f"Failed to extract annotations from PDF: {str(e)}")
        
        return urls
    
    async def _extract_from_text(self, pdf_path: str) -> Set[str]:
        """Extract URLs from PDF text content using multiple extraction methods."""
        urls = set()
        
        # Try pypdf/PyPDF2 first
        text_content = await self._extract_text_with_pypdf(pdf_path)
        
        # Fallback to pdfminer if pypdf fails
        if not text_content and PDFMINER_AVAILABLE:
            text_content = await self._extract_text_with_pdfminer(pdf_path)
        
        if text_content:
            # Extract URLs using regex patterns
            for pattern in self.url_patterns:
                matches = pattern.findall(text_content)
                for match in matches:
                    # Clean up the URL
                    url = match.strip('.,;:!?)"\'')
                    if len(url) > 5:  # Minimum reasonable URL length
                        urls.add(url)
        
        return urls
    
    async def _extract_text_with_pypdf(self, pdf_path: str) -> str:
        """Extract text using pypdf/PyPDF2."""
        if PdfReader is None:
            return ""
        
        try:
            text_content = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
            
            return text_content
        
        except (PdfReadError, Exception) as e:
            logger.warning(f"pypdf text extraction failed: {str(e)}")
            return ""
    
    async def _extract_text_with_pdfminer(self, pdf_path: str) -> str:
        """Extract text using pdfminer.six (more robust for complex PDFs)."""
        if not PDFMINER_AVAILABLE:
            return ""
        
        try:
            output_string = StringIO()
            
            with open(pdf_path, 'rb') as file:
                # Set up pdfminer components
                resource_manager = PDFResourceManager()
                device = TextConverter(resource_manager, output_string, laparams=LAParams())
                
                # Extract text from all pages
                extract_text_to_fp(file, device, maxpages=0, password="", caching=True, check_extractable=True)
                
                text = output_string.getvalue()
                device.close()
                output_string.close()
                
                return text
        
        except Exception as e:
            logger.warning(f"pdfminer text extraction failed: {str(e)}")
            return ""
    
    def is_likely_url(self, text: str) -> bool:
        """Heuristic to determine if a text fragment is likely a URL."""
        if not text or len(text) < 4:
            return False
        
        # Check for obvious URL patterns
        if text.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
            return True
        
        # Check for domain patterns
        if '.' in text and not text.startswith('.') and not text.endswith('.'):
            # Simple heuristic: contains a dot and looks domain-like
            parts = text.split('.')
            if len(parts) >= 2 and all(part.isalnum() or '-' in part for part in parts):
                return True
        
        return False
