from datetime import date
import math
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from fastapi import APIRouter, Query, Depends, HTTPException
import api.core.db as coredb

router = APIRouter(prefix="/playergamelogs", tags=["playergamelogs"])


def get_mongo_db() -> AsyncIOMotorDatabase:
    db = getattr(coredb, "db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return db

def _sanitize_for_json(obj):
    # Recursively replace NaN/Inf with None
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj

@router.get("/")
async def list_player_gamelogs(
    player_id: Optional[int] = Query(None, description="Filter by PLAYER_ID"),
    team_id: Optional[int] = Query(None, description="Filter by TEAM_ID"),
    game_id: Optional[str] = Query(None, description="Filter by GAME_ID"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD (filters by GAME_DATE)"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD (filters by GAME_DATE)"),
    limit: int = Query(100, ge=1, le=5000),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("GAME_DATE", description="Field to sort by"),
    sort_dir: int = Query(-1, description="1 asc, -1 desc"),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    coll = mongo["player_game_logs"]

    filt = {}
    if player_id is not None:
        filt["PLAYER_ID"] = int(player_id)
    if team_id is not None:
        filt["TEAM_ID"] = int(team_id)
    if game_id is not None:
        filt["GAME_ID"] = str(game_id)
    if start_date or end_date:
        rng = {}
        if start_date:
            rng["$gte"] = start_date
        if end_date:
            rng["$lte"] = end_date
        filt["GAME_DATE"] = rng

    total = await coll.count_documents(filt)
    cursor = (
        coll.find(filt)
        .sort([(sort_by, sort_dir)])
        .skip(skip)
        .limit(limit)
    )
    items = await cursor.to_list(length=limit)
    for it in items:
        it["_id"] = str(it["_id"])
    items = [_sanitize_for_json(it) for it in items]  # sanitize

    return {
        "total": total,
        "count": len(items),
        "skip": skip,
        "limit": limit,
        "items": items,
    }

@router.get("/paged")
async def list_player_gamelogs_paged(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(100, ge=1, le=5000, description="Items per page"),
    sort_by: str = Query("GAME_DATE", description="Field to sort by"),
    sort_dir: int = Query(-1, description="1 asc, -1 desc"),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    coll = mongo["player_game_logs"]

    total = await coll.count_documents({})
    total_pages = max((total + per_page - 1) // per_page, 1)
    page = min(page, total_pages)
    skip = (page - 1) * per_page

    cursor = (
        coll.find({})
        .sort([(sort_by, sort_dir)])
        .skip(skip)
        .limit(per_page)
    )
    items = await cursor.to_list(length=per_page)
    for it in items:
        it["_id"] = str(it["_id"])
    items = [_sanitize_for_json(it) for it in items]  # sanitize

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "items": items,
    }