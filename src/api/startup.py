from datetime import date
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from api.core.db import init_db
from api.fetchers import sync_teams, sync_players, sync_games, sync_player_gamelogs

load_dotenv()
async def startup_event() -> None:
    """Function to run at application startup."""
    await initialize_db()
    from api.core.db import db
    await sync_initial_data(db)


async def initialize_db() -> None:
    """Initialize the database connection."""
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")
    
    if not MONGO_URI or not DB_NAME:
        print("Database: Failed to initialize ❌")
        raise ValueError("MONGO_URI and DB_NAME must be set in environment variables.")

    init_db(MONGO_URI, DB_NAME)
    
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        await client.server_info()
    except PyMongoError as e:
        print("Database: Failed to initialize ❌")
        print(f"Database connection error: {e}")
        raise
    except Exception as e:
        print("Database: Failed to initialize ❌")
        print(f"Unexpected error: {e}")
        raise
    
    print("Database: Initalized ✅")
    
async def sync_initial_data(db) -> None:
    """Sync initial data into the database."""
    
    teams_synced = await sync_teams(db)
    print("Teams: No new teams to sync ✅" if teams_synced == 0 else f"Teams: Synced {teams_synced} new teams ✅")
    
    players_synced = await sync_players(db, active_only=True)
    print("Players: No new players to sync ✅" if players_synced == 0 else f"Players: Synced {players_synced} new players ✅")
    
    start_date = os.getenv("EARLIEST_DATE")
    if not start_date:
        start_date = "2010-10-01"
    games_synced = await sync_games(db, start_date=start_date, end_date=date.today())
    print("Games: No new games to sync ✅" if games_synced == 0 else f"Games: Synced {games_synced} new games ✅")
    ### Important: New games should trigger other data syncs in future (e.g., stats, predictions) ###
    games_count = await db["games"].estimated_document_count()
    pgl_count = await db["player_game_logs"].estimated_document_count()
    if games_count > pgl_count:
        pgl_synced = await sync_player_gamelogs(db, start_date=start_date, end_date=date.today(), show_progress=True)
        print("PlayerGameLogs: No new logs to sync ✅" if pgl_synced == 0 else f"PlayerGameLogs: Synced {pgl_synced} new logs ✅")
    else:
        print("PlayerGameLogs: Up to date ✅")
    