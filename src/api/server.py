from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from .db import Base, engine
from .db.engine import AsyncSessionLocal
from .routes import games, players, teams
from .utils.seasons import get_current_season

scheduler = AsyncIOScheduler()


async def sync_data():
    """
    Asynchronously synchronizes application data (teams, players, and games) for the current season.
    This coroutine:
    - Determines the current season via get_current_season().
    - Opens an asynchronous database session using AsyncSessionLocal() and passes it to each sync operation.
    - Calls teams.sync_teams(db) to ensure team records are up to date.
    - Calls players.sync_players(db) to ensure player records are up to date.
    - Re-evaluates the current season and calls games.sync_all_seasons(db) to synchronize game data (the implementation invokes synchronization for all relevant seasons).
    - Emits simple console log messages (prints) to indicate progress and success.
    - Catches any Exception raised during the sync operations and logs an error message instead of propagating the exception.
    Notes:
    - This function is intended to be awaited (e.g., scheduled or invoked from an async event loop).
    - The function does not return a value; it returns None.
    - Exceptions raised outside the inner try block (for example, during AsyncSessionLocal() context entry) may still propagate.
    Returns:
        None
    """
    season = get_current_season()
    print(f"🔄 Auto-syncing games for current season: {season}")

    async with AsyncSessionLocal() as db:
        try:
            print("👥 Syncing teams...")
            await teams.sync_teams(db)

            print("🏀 Syncing players...")
            await players.sync_players(db)

            season = get_current_season()
            print(f"🎮 Syncing games for {season}...")
            await games.sync_all_seasons(db)

            print("✅ All data synced!")
        except Exception as e:
            print(f"❌ Error auto-syncing: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async lifespan function for FastAPI.
    This coroutine acts as the application's lifespan/context manager. On startup it:
    - Prints a startup message to stdout.
    - Initializes the database schema by running Base.metadata.create_all within an asynchronous engine transaction.
    - Registers a recurring job (sync_current_season_games) with the scheduler to run every 6 hours (cron: hour="*/6"),
        using id="sync_current_season" and replace_existing=True.
    - Starts the scheduler and prints a confirmation message.
    The function then yields control to allow the FastAPI application to run. On shutdown it:
    - Prints a shutdown message.
    - Disposes the asynchronous database engine (await engine.dispose()).
    - Prints a confirmation that the database connection was closed.
    Parameters:
            app (FastAPI): The FastAPI application instance.
    Side effects:
    - Creates database tables if they do not exist.
    - Schedules and starts a background job that runs periodically.
    - Writes status messages to stdout.
    - Closes the database connection on shutdown.
    Dependencies/assumptions:
    - Relies on module-level objects: `engine`, `Base`, `scheduler`, and `sync_current_season_games`.
    - Intended to be passed as the FastAPI lifespan handler (e.g., FastAPI(lifespan=lifespan)).
    """

    print("🚀 Starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database initialized")

    print("📊 Running initial sync...")
    await sync_data()

    scheduler.add_job(
        sync_data,
        "cron",
        hour="*/6",
        id="sync_current_season",
        replace_existing=True,
    )
    scheduler.start()
    print("⏱️  Scheduler started - syncing every 6 hours")

    yield

    print("🛑 Shutting down...")
    scheduler.shutdown()
    await engine.dispose()
    print("✓ Database connection closed")


app = FastAPI(
    debug=True,
    title="NBA Middleware API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """
    Asynchronously return basic health information for the server.

    Returns a dict with the following keys:
    - status (str): Service health status, always "ok" when reachable.
    - current_season: Value returned by get_current_season(), representing the active season/context.
    - next_sync (datetime | None): The next scheduled run time of the "sync_current_season" job from the scheduler,
        or None if that job is not scheduled.

    Returns:
            dict: Health information as described above.

    Examples:
            >>> await health()
            {"status": "ok", "current_season": <season>, "next_sync": datetime.datetime(...)}
    """
    return {
        "status": "ok",
        "current_season": get_current_season(),
        "next_sync": (
            scheduler.get_job("sync_current_season").next_run_time
            if scheduler.get_job("sync_current_season")
            else None
        ),
    }


app.include_router(teams.router)
app.include_router(players.router)
app.include_router(games.router)
