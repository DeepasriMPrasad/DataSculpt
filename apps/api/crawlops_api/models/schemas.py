from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator

class ErrorCode(str, Enum):
    """Error codes for API responses."""
    AUTH_REQUIRED = "AUTH_REQUIRED"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED" 
    TIMEOUT = "TIMEOUT"
    ROBOTS_BLOCKED = "ROBOTS_BLOCKED"
    SINGLEFILE_ERROR = "SINGLEFILE_ERROR"
    EXTRACT_ERROR = "EXTRACT_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    PDF_PARSE_ERROR = "PDF_PARSE_ERROR"

class ExecutionProfile(str, Enum):
    """Execution profile types."""
    STANDARD = "standard"
    SAFE = "safe"  
    GUIDED = "guided"

class URLItemStatus(str, Enum):
    """URL item status types."""
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_CAPTCHA = "waiting_captcha"
    WAITING_USER = "waiting_user"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"

# Request Models
class ExtractRequest(BaseModel):
    """Request model for content extraction."""
    url: str = Field(..., description="Target URL to extract content from")
    timeout: int = Field(30, ge=5, le=300, description="Request timeout in seconds")
    user_agent: Optional[str] = Field(None, description="Custom user agent string")
    wait_for: Optional[str] = Field(None, description="CSS selector to wait for before extracting")
    css_selector: Optional[str] = Field(None, description="CSS selector for targeted extraction")
    word_count_threshold: int = Field(10, ge=0, description="Minimum word count for content")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class PDFLinksRequest(BaseModel):
    """Request model for PDF link extraction."""
    pdf_path: str = Field(..., description="Absolute path to PDF file")
    base_url: Optional[str] = Field(None, description="Base URL for resolving relative links")
    extract_from_text: bool = Field(True, description="Extract URLs from text content")
    extract_from_annotations: bool = Field(True, description="Extract URLs from PDF annotations")

class ExportRequest(BaseModel):
    """Request model for report export."""
    format: str = Field(..., pattern="^(csv|json)$", description="Export format")
    path: str = Field(..., description="Output file path")
    run_id: Optional[str] = Field(None, description="Specific run ID to export (all runs if not specified)")

# Response Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field("ok", description="Service status")
    message: str = Field("", description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExtractError(BaseModel):
    """Error response for extraction failures."""
    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")

class ExtractMeta(BaseModel):
    """Metadata for extracted content."""
    title: str = Field("", description="Page title")
    description: str = Field("", description="Page description")
    status: int = Field(200, description="HTTP status code")
    content_type: str = Field("text/html", description="Content type")
    word_count: int = Field(0, description="Word count of extracted content")
    processing_time: float = Field(0.0, description="Processing time in seconds")
    links_found: int = Field(0, description="Number of links found")
    images_found: int = Field(0, description="Number of images found")

class ExtractResponse(BaseModel):
    """Response model for content extraction."""
    url: str = Field(..., description="Original URL")
    json: Dict[str, Any] = Field(default_factory=dict, description="Structured JSON data")
    markdown: str = Field("", description="Markdown content")
    meta: ExtractMeta = Field(..., description="Extraction metadata")

class PDFLinksResponse(BaseModel):
    """Response model for PDF link extraction."""
    url_count: int = Field(..., description="Number of URLs found")
    urls: List[str] = Field(..., description="List of extracted URLs")
    extraction_methods: List[str] = Field(default_factory=list, description="Methods used for extraction")
    file_info: Dict[str, Any] = Field(default_factory=dict, description="PDF file information")

class ExportResponse(BaseModel):
    """Response model for report export."""
    ok: bool = Field(..., description="Export success status")
    path: str = Field(..., description="Output file path")
    format: str = Field(..., description="Export format used")
    records_exported: int = Field(0, description="Number of records exported")

# Domain Models
class URLItemFormats(BaseModel):
    """URL item format options."""
    json: bool = Field(False, description="Extract JSON data")
    md: bool = Field(False, description="Extract markdown")
    html: bool = Field(False, description="Generate SingleFile HTML")
    pdf: bool = Field(False, description="Generate PDF")

class URLItemOutputs(BaseModel):
    """URL item output file paths."""
    jsonPath: Optional[str] = Field(None, description="Path to JSON output")
    mdPath: Optional[str] = Field(None, description="Path to markdown output") 
    singlefileHtmlPath: Optional[str] = Field(None, description="Path to SingleFile HTML")
    pdfPath: Optional[str] = Field(None, description="Path to PDF output")

class URLItem(BaseModel):
    """Individual URL item in the crawl queue."""
    url: str = Field(..., description="Target URL")
    depth: int = Field(0, ge=0, description="Crawl depth")
    status: URLItemStatus = Field(URLItemStatus.QUEUED, description="Current status")
    formats: URLItemFormats = Field(default_factory=URLItemFormats, description="Requested formats")
    attempts: int = Field(0, ge=0, description="Number of attempts")
    error: Optional[str] = Field(None, description="Last error message")
    outputs: Optional[URLItemOutputs] = Field(None, description="Output file paths")
    profile: ExecutionProfile = Field(ExecutionProfile.STANDARD, description="Execution profile")
    startedAt: Optional[datetime] = Field(None, description="Start time")
    finishedAt: Optional[datetime] = Field(None, description="Finish time")

class QueueStats(BaseModel):
    """Queue statistics."""
    running: int = Field(0, ge=0, description="Number of running items")
    waiting: int = Field(0, ge=0, description="Number of waiting items")
    done: int = Field(0, ge=0, description="Number of completed items")
    failed: int = Field(0, ge=0, description="Number of failed items") 
    total: int = Field(0, ge=0, description="Total number of items")

class RunKPIs(BaseModel):
    """Key performance indicators for a crawl run."""
    pages_per_hour: float = Field(0.0, ge=0, description="Pages processed per hour")
    success_rate: float = Field(0.0, ge=0, le=1, description="Success rate (0-1)")
    average_processing_time: float = Field(0.0, ge=0, description="Average processing time per page")
    total_bytes: int = Field(0, ge=0, description="Total bytes downloaded")

class CrawlSettings(BaseModel):
    """Crawl configuration settings."""
    startUrl: str = Field(..., description="Starting URL")
    depth: int = Field(2, ge=1, le=10, description="Maximum crawl depth")
    maxPages: int = Field(100, ge=1, description="Maximum pages to crawl")
    allowedDomains: List[str] = Field(default_factory=list, description="Allowed domains")
    disallowedPaths: List[str] = Field(default_factory=list, description="Disallowed path patterns")
    concurrency: int = Field(3, ge=1, le=10, description="Concurrent requests")
    delay: int = Field(1000, ge=0, description="Delay between requests (ms)")
    respectRobots: bool = Field(True, description="Respect robots.txt")
    outputDirectory: str = Field("", description="Output directory path")
    formats: URLItemFormats = Field(default_factory=URLItemFormats, description="Output formats")
    crawlPdfLinks: bool = Field(False, description="Crawl links found in PDFs")
    profile: ExecutionProfile = Field(ExecutionProfile.STANDARD, description="Execution profile")
    proxy: Optional[Dict[str, str]] = Field(None, description="Proxy configuration")
    caBundlePath: Optional[str] = Field(None, description="CA bundle path")

class RunReport(BaseModel):
    """Complete report for a crawl run."""
    id: str = Field(..., description="Unique run identifier")
    start_time: datetime = Field(..., description="Run start time")
    end_time: Optional[datetime] = Field(None, description="Run end time")
    profile: ExecutionProfile = Field(..., description="Execution profile used")
    settings: CrawlSettings = Field(..., description="Crawl settings used")
    items: List[URLItem] = Field(default_factory=list, description="Crawled items")
    stats: QueueStats = Field(default_factory=QueueStats, description="Queue statistics")
    kpis: RunKPIs = Field(default_factory=RunKPIs, description="Key performance indicators")

class ReportSummary(BaseModel):
    """Summary information for a crawl run."""
    id: str = Field(..., description="Run identifier")
    start_time: datetime = Field(..., description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    profile: ExecutionProfile = Field(..., description="Execution profile")
    total_items: int = Field(0, description="Total items processed")
    success_rate: float = Field(0.0, description="Success rate")
    pages_per_hour: float = Field(0.0, description="Pages per hour")

class ChallengeInfo(BaseModel):
    """Information about a crawl challenge."""
    url: str = Field(..., description="URL that triggered the challenge")
    type: str = Field(..., pattern="^(captcha|auth|manual)$", description="Challenge type")
    provider: Optional[str] = Field(None, description="Challenge provider (e.g., recaptcha)")
    screenshotPath: Optional[str] = Field(None, description="Path to screenshot")

class UserAction(BaseModel):
    """User action in response to a challenge."""
    action: str = Field(..., pattern="^(continue|retry|skip|abort)$", description="Action to take")
    overrides: Optional[Dict[str, Union[int, float]]] = Field(None, description="Setting overrides")

class ProfileConfig(BaseModel):
    """Configuration for an execution profile."""
    concurrency: int = Field(3, ge=1, le=10, description="Concurrent requests")
    delay: int = Field(1000, ge=0, description="Delay between requests (ms)")
    jitter: int = Field(500, ge=0, description="Random delay jitter (ms)")
    respectRobots: bool = Field(True, description="Respect robots.txt")
    timeout: int = Field(30, ge=5, le=300, description="Request timeout (seconds)")
    retries: int = Field(3, ge=0, le=10, description="Maximum retries")
    backoffMultiplier: float = Field(2.0, ge=1.0, description="Backoff multiplier for retries")
