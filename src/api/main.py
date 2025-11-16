from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

from api.core.config import settings
from api.router.router import api_router
from api.startup import startup_event

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async context manager for application lifespan events."""
    await startup_event()
    yield
    

app = FastAPI(
    title=settings.PROJECT_NAME, 
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
