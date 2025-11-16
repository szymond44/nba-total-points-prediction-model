from motor.motor_asyncio import AsyncIOMotorClient

client = None
db = None
def init_db(uri: str, db_name:str) -> None:
    """Initialize the database with required tables."""
    global client, db
    client = AsyncIOMotorClient(uri)
    db = client[db_name]