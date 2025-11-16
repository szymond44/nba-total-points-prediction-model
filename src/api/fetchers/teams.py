from nba_api.stats.static import teams as t
from pymongo.errors import BulkWriteError

async def sync_teams(db) -> int:
    """Fetch and store NBA teams in the database. Returns number inserted."""
    nba_teams = t.get_teams()
    team_collection = db["teams"]
    await team_collection.create_index("id", unique=True)
    
    incoming_by_id = {team["id"]: team for team in nba_teams}
    incoming_ids = set(incoming_by_id.keys())

    existing_ids = set(await team_collection.distinct("id", {"id": {"$in": list(incoming_ids)}}))
    missing_ids = incoming_ids - existing_ids

    if not missing_ids:
        return 0 
    
    docs = []
    for tid in missing_ids:
        team = incoming_by_id[tid]
        docs.append({
            "id": team["id"],
            "full_name": team.get("full_name"),
            "abbreviation": team.get("abbreviation"),
            "nickname": team.get("nickname"),
            "city": team.get("city"),
            "state": team.get("state"),
            "year_founded": team.get("year_founded"),
        })

    try:
        result = await team_collection.insert_many(docs, ordered=False)
        return len(result.inserted_ids)
    except BulkWriteError:
        return len(docs)