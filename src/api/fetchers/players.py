from nba_api.stats.static import players as p
from pymongo.errors import BulkWriteError

async def sync_players(db, active_only: bool = True) -> int:
    """Fetch NBA players and insert only those missing. Returns the number inserted."""
    players = p.get_players()
    if active_only:
        players = [pl for pl in players if pl.get("is_active")]

    collection = db["players"]
    await collection.create_index("id", unique=True)

    incoming_by_id = {pl["id"]: pl for pl in players}
    if not incoming_by_id:
        return 0

    incoming_ids = set(incoming_by_id.keys())
    existing_ids = set(await collection.distinct("id", {"id": {"$in": list(incoming_ids)}}))
    missing_ids = incoming_ids - existing_ids

    if not missing_ids:
        return 0

    docs = []
    for pid in missing_ids:
        pl = incoming_by_id[pid]
        docs.append({
            "id": pl["id"],
            "full_name": pl.get("full_name"),
            "first_name": pl.get("first_name"),
            "last_name": pl.get("last_name"),
            "is_active": pl.get("is_active"),
        })

    try:
        result = await collection.insert_many(docs, ordered=False)
        return len(result.inserted_ids)
    except BulkWriteError:
        return len(docs)