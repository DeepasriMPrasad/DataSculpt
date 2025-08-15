import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

from ..models.schemas import (
    ExtractRequest, 
    ExtractResponse, 
    ExtractError,
    ErrorCode
)
from ..services.crawl4ai_service import Crawl4aiService
from ..services.singlefile_service import capture_singlefile

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize crawl4ai service
crawl_service = Crawl4aiService()

@router.post("/extract", response_model=ExtractResponse)
async def extract_content(request: ExtractRequest, background_tasks: BackgroundTasks):
    """
    Extract content from a URL using crawl4ai.
    
    Returns JSON data, markdown content, and metadata.
    """
    try:
        logger.info(f"Starting extraction for URL: {request.url}")
        
        # Validate URL
        if not request.url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400,
                detail=ExtractError(
                    code=ErrorCode.HTTP_ERROR,
                    message="Invalid URL format. Must start with http:// or https://",
                    details={"url": request.url}
                ).dict()
            )
        
        # Extract content using crawl4ai
        result = await crawl_service.extract_content(
            url=request.url,
            timeout=request.timeout,
            user_agent=request.user_agent,
            wait_for=request.wait_for,
            css_selector=request.css_selector,
            word_count_threshold=request.word_count_threshold
        )
        
        logger.info(f"Successfully extracted content from {request.url}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=ExtractError(
                code=ErrorCode.HTTP_ERROR,
                message=str(e),
                details={"url": request.url}
            ).dict()
        )
        
    except TimeoutError as e:
        logger.error(f"Timeout error for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=408,
            detail=ExtractError(
                code=ErrorCode.TIMEOUT,
                message="Request timed out",
                details={"url": request.url, "timeout": request.timeout}
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"Extraction failed for {request.url}: {str(e)}")
        
        # Determine error type
        error_message = str(e).lower()
        if 'auth' in error_message or '401' in error_message or '403' in error_message:
            code = ErrorCode.AUTH_REQUIRED
        elif 'captcha' in error_message or 'recaptcha' in error_message:
            code = ErrorCode.CAPTCHA_REQUIRED
        elif 'robots' in error_message or 'disallow' in error_message:
            code = ErrorCode.ROBOTS_BLOCKED
        else:
            code = ErrorCode.EXTRACT_ERROR
            
        raise HTTPException(
            status_code=500,
            detail=ExtractError(
                code=code,
                message=f"Failed to extract content: {str(e)}",
                details={"url": request.url}
            ).dict()
        )

@router.post("/singlefile")
async def capture_singlefile_html(request: ExtractRequest):
    """
    Capture a complete webpage with SingleFile integration.
    
    Returns the complete HTML with all CSS and images inlined.
    """
    try:
        logger.info(f"Starting SingleFile capture for URL: {request.url}")
        
        # Validate URL
        if not request.url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400,
                detail=ExtractError(
                    code=ErrorCode.HTTP_ERROR,
                    message="Invalid URL format. Must start with http:// or https://",
                    details={"url": request.url}
                ).dict()
            )
        
        # Capture page with SingleFile
        result = await capture_singlefile(request.url)
        
        logger.info(f"Successfully captured SingleFile HTML from {request.url}")
        return {
            "url": request.url,
            "html": result['html'],
            "size_bytes": result['size_bytes'],
            "resources_inlined": result['resources_inlined'],
            "original_url": result['original_url']
        }
        
    except Exception as e:
        logger.error(f"SingleFile capture failed for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ExtractError(
                code=ErrorCode.UNKNOWN_ERROR,
                message=f"SingleFile capture failed: {str(e)}",
                details={"error": str(e), "url": request.url}
            ).dict()
        )


@router.get("/status")
async def extraction_status():
    """Get extraction service status."""
    return {
        "status": "operational",
        "service": "crawl4ai",
        "ready": await crawl_service.is_ready()
    }
