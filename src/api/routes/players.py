from fastapi import APIRouter, Depends
from nba_api.stats.static import players as nba_players
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from ..db import get_db
from ..models.player import Player

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/sync")
async def sync_players(db: AsyncSession = Depends(get_db)):
    players = nba_players.get_players()
    print(f"📊 Found {len(players)} players")

    # Progress bar na console
    for player_info in tqdm(players, desc="Syncing players", unit="player"):
        existing = await db.execute(
            select(Player).where(Player.id == player_info["id"])
        )
        existing_player = existing.scalar_one_or_none()

        if existing_player:
            existing_player.full_name = player_info["full_name"]
            existing_player.first_name = player_info["first_name"]
            existing_player.last_name = player_info["last_name"]
            existing_player.is_active = player_info["is_active"]
        else:
            player = Player(
                id=player_info["id"],
                full_name=player_info["full_name"],
                first_name=player_info["first_name"],
                last_name=player_info["last_name"],
                is_active=player_info["is_active"],
            )
            db.add(player)

    await db.commit()
    return {"message": f"Synced {len(players)} players"}


@router.get("/")
async def get_players(db: AsyncSession = Depends(get_db)):
    """Pobierz wszystkich graczy z bazy"""
    result = await db.execute(select(Player))
    players = result.scalars().all()

    return {
        "players": [
            {
                "id": p.id,
                "full_name": p.full_name,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "is_active": p.is_active,
            }
            for p in players
        ]
    }
