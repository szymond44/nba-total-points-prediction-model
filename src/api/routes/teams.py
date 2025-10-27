from fastapi import APIRouter, Depends
from nba_api.stats.static import teams as nba_teams
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from ..db import get_db

# from ..fetchers.team_info_common import TeamInfoCommonFetcher
from ..models.team import Team

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/sync")
async def sync_teams(db: AsyncSession = Depends(get_db)):
    teams = nba_teams.get_teams()
    for team_info in tqdm(teams, desc="Syncing teams", unit="team"):
        existing = await db.execute(select(Team).where(Team.id == team_info["id"]))
        existing_team = existing.scalar_one_or_none()

        if existing_team:
            existing_team.name = team_info["full_name"]
            existing_team.abbreviation = team_info["abbreviation"]
            existing_team.nickname = team_info["nickname"]
            existing_team.city = team_info["city"]
            existing_team.state = team_info["state"]
            existing_team.year_founded = team_info["year_founded"]
        else:
            team = Team(
                id=team_info["id"],
                name=team_info["full_name"],
                abbreviation=team_info["abbreviation"],
                nickname=team_info["nickname"],
                city=team_info["city"],
                state=team_info["state"],
                year_founded=team_info["year_founded"],
            )
            db.add(team)

    await db.commit()
    return {"message": f"Synced {len(teams)} teams"}


@router.get("/")
async def get_teams(db: AsyncSession = Depends(get_db)):
    """Pobierz wszystkie drużyny z bazy"""

    result = await db.execute(select(Team))
    teams = result.scalars().all()

    return {
        "teams": [
            {
                "id": t.id,
                "name": t.name,
                "abbreviation": t.abbreviation,
                "nickname": t.nickname,
                "city": t.city,
                "state": t.state,
                "year_founded": t.year_founded,
            }
            for t in teams
        ]
    }
