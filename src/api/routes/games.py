import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends
from nba_api.stats.endpoints import leaguegamelog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from ..db import get_db
from ..models.game import Game
from ..models.team import Team
from ..utils.seasons import (
    get_current_season,
    get_season_range,
    get_season_range_reverse,
)

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/seasons")
async def get_seasons():
    """
    Asynchronously collect and return season information for the API.
    This function aggregates season data from helper functions and returns a
    serializable mapping suitable for an API response.
    Returns:
        dict: A mapping with the following keys:
            - "total" (int): Number of seasons returned by get_season_range().
            - "current_season": The current season value as returned by get_current_season().
            - "seasons" (list): The list of seasons as returned by get_season_range().
    Notes:
        - The exact structure and types of items in "seasons" and "current_season"
          depend on the implementations of get_season_range() and get_current_season().
        - This coroutine does not perform I/O itself; it delegates to the helper functions.
    """
    seasons = get_season_range()

    return {
        "total": len(seasons),
        "current_season": get_current_season(),
        "seasons": seasons,
    }


@router.get("/all")
async def get_all_games(db: AsyncSession = Depends(get_db)):
    """
    Asynchronous FastAPI route handler that retrieves all Game records from the database,
    groups them by season, and returns summary metadata and grouped game details.
    Args:
        db (sqlalchemy.ext.asyncio.AsyncSession, optional): Asynchronous SQLAlchemy session
            injected via FastAPI Depends(get_db). Used to query the Game table.
    Returns:
        dict: A dictionary with the following structure:
                "total_games": int,       # total number of games returned
                "total_seasons": int,     # number of distinct seasons present
                "current_season": Any,    # value returned by get_current_season()
                "games_by_season": {      # mapping of season -> list of game dicts
                    season_value: [
                            "game_id": Any,     # Game.game_id
                            "team_id": Any,     # Game.team_id
                            "date": str,        # ISO 8601 formatted date (game.game_date.isoformat())
                            "result": Any,      # Game.result
                            "points": Any,      # Game.points
                            "plus_minus": Any,  # Game.plus_minus
                        },
                        ...
                    ],
                    ...
    Behavior and notes:
        - Games are queried ordered by Game.game_date descending.
        - The function groups games in memory by the Game.season attribute.
        - Dates are returned as ISO-8601 strings via game.game_date.isoformat().
        - Database errors raised by the underlying SQLAlchemy/DB driver (e.g., connection errors)
          are propagated to the caller; this function does not perform exception handling itself.
        - This is intended to be used as a FastAPI dependency endpoint handler and expects
          the Game model to expose the listed attributes.
    """
    result = await db.execute(select(Game).order_by(Game.game_date.desc()))
    games = result.scalars().all()

    games_by_season = {}
    for game in games:
        if game.season not in games_by_season:
            games_by_season[game.season] = []

        games_by_season[game.season].append(
            {
                "game_id": game.game_id,
                "team_id": game.team_id,
                "date": game.game_date.isoformat(),
                "result": game.result,
                "points": game.points,
                "plus_minus": game.plus_minus,
            }
        )

    return {
        "total_games": len(games),
        "total_seasons": len(games_by_season),
        "current_season": get_current_season(),
        "games_by_season": games_by_season,
    }


@router.get("/sync-all")
async def sync_all_seasons(db: AsyncSession = Depends(get_db)):
    """
    Asynchronously synchronize games for all seasons returned by get_season_range_reverse().
    This coroutine:
    - Obtains a list of seasons from get_season_range_reverse() (expected in reverse chronological order).
    - Prints a summary line describing how many seasons will be processed and the range (oldest to newest).
    - Iterates over the seasons using tqdm to display a progress bar.
    - For each season, calls await sync_games(season, db, tqdm_disable=True) to perform the per-season synchronization.
    - Catches and logs (via print) any exception raised while syncing an individual season, allowing the loop to continue with remaining seasons.
    - Returns a simple JSON-serializable dict indicating how many seasons were processed.
    Parameters:
    - db: AsyncSession
        Asynchronous database session provided via dependency injection (Depends(get_db)).
    Returns:
    - dict
        A dictionary of the form {"message": "Synced N seasons"} where N is the number of seasons processed.
    Side effects:
    - Prints informational and error messages to stdout.
    - Displays a tqdm progress bar for the season loop.
    - Calls external helpers: get_season_range_reverse() and sync_games(...).
    - Exceptions thrown during individual season syncs are caught and printed; they do not abort the overall synchronization.
    Notes:
    - This function is an async endpoint/coroutine and must be awaited by the caller or used by an async framework (e.g., FastAPI).
    - Because exceptions per season are swallowed (only logged), callers should consult logs/console for details about any failed season syncs.
    """
    seasons = get_season_range_reverse()

    print(f"📅 Syncing {len(seasons)} seasons from {seasons[-1]} to {seasons[0]}")

    for season in tqdm(seasons, desc="Seasons", unit="season"):
        try:
            await sync_games(season, db, tqdm_disable=True)
        except Exception as e:
            print(f"❌ Error syncing {season}: {e}")

    return {"message": f"Synced {len(seasons)} seasons"}


@router.get("/sync/{season}")
async def sync_games(
    season: str, db: AsyncSession = Depends(get_db), tqdm_disable: bool = False
):
    """
    Sync games for a given NBA season into the database.
    Asynchronously fetches game logs for the provided season using nba_api.leaguegamelog.LeagueGameLog.
    The blocking API call is run in a thread executor to avoid blocking the event loop. Retrieved
    records are sorted and iterated (optionally showing a tqdm progress bar). For each record, the
    function checks whether a Game with the same game_id and team_id already exists in the provided
    AsyncSession; if not, a new Game instance is created and added to the session. The session is
    committed once all rows have been processed.
    Args:
        season (str): Season identifier accepted by nba_api.leaguegamelog.LeagueGameLog
            (e.g., "2020-21").
        db (AsyncSession): Async database session (typically injected via FastAPI Depends(get_db)).
        tqdm_disable (bool): If True, disables tqdm progress bar and suppresses the summary print.
            Defaults to False.
    Returns:
        dict: On success, returns {"message": f"Synced games for {season}"}. On error, returns
        {"error": "<exception message>"} — the function catches exceptions and returns them in this form.
    Side effects:
        - Performs network I/O to fetch game logs.
        - Adds new Game objects to the AsyncSession and commits the transaction.
        - Parses game dates using datetime.strptime(row["GAME_DATE"], "%Y-%m-%d") and casts TEAM_ID to int.
    Notes:
        - The existence check (select ... where game_id == ... and team_id == ...) is performed in
          application code; for safety under concurrent execution, enforce a unique constraint on
          (game_id, team_id) at the database level to prevent duplicates.
        - Intended to be run within an async FastAPI route or other async context with a configured
          AsyncSession.
    """
    try:
        loop = asyncio.get_event_loop()

        games_data = await loop.run_in_executor(
            None,
            lambda: leaguegamelog.LeagueGameLog(
                season=season, league_id="00"  # 00 = NBA only
            ).get_data_frames()[0],
        )

        games_data = games_data.sort_values(
            by=["GAME_ID", "GAME_DATE"], ascending=[True, False]
        )
        if not tqdm_disable:
            print(f"📊 Found {len(games_data)} game records for {season}")

        for _, row in tqdm(
            games_data.iterrows(),
            total=len(games_data),
            desc="Syncing games",
            disable=tqdm_disable,
        ):
            existing = await db.execute(
                select(Game).where(
                    (Game.game_id == row["GAME_ID"]) & (Game.team_id == row["TEAM_ID"])
                )
            )
            existing_game = existing.scalar_one_or_none()

            if not existing_game:
                game = Game(
                    game_id=row["GAME_ID"],
                    season=season,
                    game_date=datetime.strptime(row["GAME_DATE"], "%Y-%m-%d"),
                    team_id=int(row["TEAM_ID"]),
                    result=row["WL"],
                    points=row["PTS"],
                    plus_minus=row["PLUS_MINUS"],
                )
                db.add(game)

        await db.commit()
        return {"message": f"Synced games for {season}"}

    except Exception as e:
        return {"error": str(e)}


@router.get("/{season}")
async def get_games(season: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve all games for a given season.
    This asynchronous route handler queries the database for Game records matching
    the provided season and returns a JSON-serializable summary.
    Parameters
    ----------
    season : str
        Season identifier to filter games by (e.g. "2023", "2023-2024").
    db : AsyncSession
        Asynchronous SQLAlchemy session injected via Depends(get_db).
    Returns
    -------
    dict
        A dictionary with the following structure:
            "season": str,           # the requested season
            "total_games": int,      # number of games returned
            "games": [               # list of game objects
                    "game_id": Any,      # primary id of the game record
                    "team_id": Any,      # id of the team
                    "date": str,         # game_date formatted as ISO 8601 string
                    "result": Any,       # game result (as stored on the model)
                    "points": Any,       # points scored/awarded
                    "plus_minus": Any,   # plus/minus value
                },
                ...
    Notes
    -----
    - If no games are found for the season, "total_games" will be 0 and "games" will be an empty list.
    - The "date" field is produced via datetime.isoformat() and is safe for JSON serialization.
    - Database-related errors may be raised by the underlying AsyncSession.execute call.
    """
    result = await db.execute(select(Game).where(Game.season == season))
    games = result.scalars().all()

    return {
        "season": season,
        "total_games": len(games),
        "games": [
            {
                "game_id": g.game_id,
                "team_id": g.team_id,
                "date": g.game_date.isoformat(),
                "result": g.result,
                "points": g.points,
                "plus_minus": g.plus_minus,
            }
            for g in games
        ],
    }
