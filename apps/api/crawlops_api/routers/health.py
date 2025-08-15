from fastapi import APIRouter
from ..models.schemas import HealthResponse

router = APIRouter()

@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        message="CrawlOps API is healthy"
    )
