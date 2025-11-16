from fastapi import APIRouter


router = APIRouter(prefix="/info", tags=["info"])

@router.get("/version", summary="Get API version")
async def get_api_version():
    """Endpoint to get the current API version."""
    return {"version": "1.0.0"}

@router.get("/health", summary="Health check endpoint")
async def health_check():
    """Endpoint to check the health of the API."""
    return {"status": "healthy"}