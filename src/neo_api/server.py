from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous lifespan context manager for a FastAPI application.
    This async generator performs application startup and shutdown tasks related to
    database lifecycle management.
    Behavior
    - Startup:
        - Prints a startup message to stdout.
        - Opens an asynchronous connection transaction on the global `engine`
            and runs `Base.metadata.create_all` to ensure database tables are created.
    - Yield:
        - Yields control back to FastAPI so the application can run normally after
            initialization is complete.
    - Shutdown:
        - Prints a shutdown message to stdout.
        - Disposes the global `engine` to close any remaining database connections.
    Parameters
    - app (FastAPI): The FastAPI application instance that this lifespan is bound to.
    Yields
    - None: Control is yielded to the FastAPI runtime while the application is running.
    Exceptions
    - Any exception raised during database initialization (create_all) or engine
        disposal will propagate to the FastAPI runtime.
    Notes
    - Assumes `engine` (an SQLAlchemy AsyncEngine) and `Base` (declarative metadata)
        exist in the module scope where this function is defined.
    - Intended to be provided to FastAPI via the `lifespan` parameter:
            app = FastAPI(lifespan=lifespan)
    - Side effects include printing to stdout and creating database tables.
    """
    # Startup
    print("🚀 Starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database initialized")
    
    yield 
    
    # Shutdown
    print("🛑 Shutting down...")
    await engine.dispose()
    print("✓ Database connection closed")

app = FastAPI(
    debug=True,
    title="NBA Middleware API",
    version="0.1.0",
    lifespan=lifespan  # ← pass lifespan here
)

@app.get("/health")
async def health():
    """
    Return basic service health information.

    Asynchronous health-check endpoint intended for monitoring and readiness/liveness probes.
    This function performs no side effects and returns a minimal payload describing the current
    service state.

    Returns:
        dict: A dictionary containing:
            - "status" (str): Health status, typically "ok" when the service is operational.
            - "version" (str): The service version (e.g., "0.1.0").
    """
    return {"status": "ok", "version": "0.1.0"}

# TODO: routers
# from src.neo_api.routes import game_logs, teams, players
# app.include_router(game_logs.router)
# app.include_router(teams.router)
# app.include_router(players.router)
