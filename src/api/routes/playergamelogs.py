import asyncio

from fastapi import APIRouter, Depends
from nba_api.stats.endpoints import playergamelogs
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from ..db import get_db
from ..models.game import Game
from ..models.playergamelogs import PlayerGameLog
from ..utils.seasons import get_season_range_reverse

router = APIRouter(prefix="/playergamelogs", tags=["playergamelogs"])


@router.get("/sync-all")
async def sync_all_player_game_logs(db: AsyncSession = Depends(get_db)):
    """Synchronizuj player game logs dla wszystkich sezonów"""
    seasons = get_season_range_reverse()

    print(f"📅 Syncing {len(seasons)} seasons from {seasons[-1]} to {seasons[0]}")

    for season in tqdm(seasons, desc="Seasons", unit="season"):
        try:
            await sync_player_game_logs(season, db, tqdm_disable=True)
        except Exception as e:
            print(f"❌ Error syncing {season}: {e}")

    return {"message": f"Synced player game logs for {len(seasons)} seasons"}


@router.get("/sync/{season}")
async def sync_player_game_logs(
    season: str, db: AsyncSession = Depends(get_db), tqdm_disable: bool = False
):
    """Synchronizuj player game logs dla sezonu"""
    try:
        loop = asyncio.get_event_loop()

        data = await loop.run_in_executor(
            None,
            lambda: playergamelogs.PlayerGameLogs(
                season_nullable=season,
                league_id_nullable="00",
                season_type_nullable="Regular Season",
            ).get_data_frames()[0],
        )

        teams_result = await db.execute(select(Game.team_id).distinct())
        valid_team_ids = set(teams_result.scalars().all())

        data = data[data["TEAM_ID"].isin(valid_team_ids)]

        if not tqdm_disable:
            print(f"📊 Found {len(data)} player game records for {season}")

        for _, row in tqdm(
            data.iterrows(),
            total=len(data),
            desc="Syncing player games",
            disable=tqdm_disable,
        ):
            # ✅ Znajdź game.id po game_id i team_id
            game_result = await db.execute(
                select(Game).where(
                    (Game.game_id == str(row["GAME_ID"]))
                    & (Game.team_id == int(row["TEAM_ID"]))
                )
            )
            game = game_result.scalar_one_or_none()

            if not game:
                print(f"⚠️ Game not found: {row['GAME_ID']} for team {row['TEAM_ID']}")
                continue

            existing = await db.execute(
                select(PlayerGameLog).where(
                    (PlayerGameLog.player_id == int(row["PLAYER_ID"]))
                    & (PlayerGameLog.game_pk_id == game.id)
                )
            )
            existing_log = existing.scalar_one_or_none()

            if not existing_log:
                log = PlayerGameLog(
                    player_id=int(row["PLAYER_ID"]),
                    game_id=str(row["GAME_ID"]),
                    team_id=int(row["TEAM_ID"]),
                    game_pk_id=game.id,
                    minutes=int(row["MIN"]),
                    fgm=int(row["FGM"]),
                    fga=int(row["FGA"]),
                    fg_pct=float(row["FG_PCT"]) if row["FG_PCT"] else None,
                    fg3m=int(row["FG3M"]),
                    fg3a=int(row["FG3A"]),
                    fg3_pct=float(row["FG3_PCT"]) if row["FG3_PCT"] else None,
                    ftm=int(row["FTM"]),
                    fta=int(row["FTA"]),
                    ft_pct=float(row["FT_PCT"]) if row["FT_PCT"] else None,
                    oreb=int(row["OREB"]),
                    dreb=int(row["DREB"]),
                    reb=int(row["REB"]),
                    ast=int(row["AST"]),
                    tov=int(row["TOV"]),
                    stl=int(row["STL"]),
                    blk=int(row["BLK"]),
                    pf=int(row["PF"]),
                    pts=int(row["PTS"]),
                )
                db.add(log)

        await db.commit()
        return {"message": f"Synced player game logs for {season}"}

    except Exception as e:
        return {"error": str(e)}


@router.get("/all")
async def get_all_player_game_logs(db: AsyncSession = Depends(get_db)):
    """Pobierz wszystkie player game logs"""
    result = await db.execute(select(PlayerGameLog))
    logs = result.scalars().all()

    logs_by_season = {}
    for log in logs:
        season_key = f"season_{log.game_id[:4]}"
        if season_key not in logs_by_season:
            logs_by_season[season_key] = []

        logs_by_season[season_key].append(
            {
                "player_id": log.player_id,
                "game_id": log.game_id,
                "team_id": log.team_id,
                "minutes": log.minutes,
                "fgm": log.fgm,
                "fga": log.fga,
                "fg_pct": log.fg_pct,
                "fg3m": log.fg3m,
                "fg3a": log.fg3a,
                "fg3_pct": log.fg3_pct,
                "ftm": log.ftm,
                "fta": log.fta,
                "ft_pct": log.ft_pct,
                "oreb": log.oreb,
                "dreb": log.dreb,
                "reb": log.reb,
                "ast": log.ast,
                "tov": log.tov,
                "stl": log.stl,
                "blk": log.blk,
                "pf": log.pf,
                "pts": log.pts,
            }
        )

    return {
        "total_logs": len(logs),
        "seasons": len(logs_by_season),
        "logs_by_season": logs_by_season,
    }


@router.get("/{season}")
async def get_player_game_logs(season: str, db: AsyncSession = Depends(get_db)):
    """Pobierz player game logs dla sezonu"""
    season_start = season.split("-")[0]

    games_result = await db.execute(
        select(Game.id).where(Game.season.like(f"{season_start}%"))
    )
    valid_game_ids = set(games_result.scalars().all())

    result = await db.execute(
        select(PlayerGameLog).where(PlayerGameLog.game_pk_id.in_(valid_game_ids))
    )
    filtered_logs = result.scalars().all()

    return {
        "season": season,
        "total_logs": len(filtered_logs),
        "logs": [
            {
                "player_id": l.player_id,
                "game_id": l.game_id,
                "team_id": l.team_id,
                "minutes": l.minutes,
                "fgm": l.fgm,
                "fga": l.fga,
                "fg_pct": l.fg_pct,
                "fg3m": l.fg3m,
                "fg3a": l.fg3a,
                "fg3_pct": l.fg3_pct,
                "ftm": l.ftm,
                "fta": l.fta,
                "ft_pct": l.ft_pct,
                "oreb": l.oreb,
                "dreb": l.dreb,
                "reb": l.reb,
                "ast": l.ast,
                "tov": l.tov,
                "stl": l.stl,
                "blk": l.blk,
                "pf": l.pf,
                "pts": l.pts,
            }
            for l in filtered_logs
        ],
    }
