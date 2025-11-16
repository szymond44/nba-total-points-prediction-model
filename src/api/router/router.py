from fastapi import APIRouter

from api.router.routes import info, playergamelogs

api_router = APIRouter()

api_router.include_router(info.router)
api_router.include_router(playergamelogs.router)