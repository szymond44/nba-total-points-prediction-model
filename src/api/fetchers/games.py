import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Union, Tuple, Iterable

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog
from pymongo.errors import BulkWriteError
from tqdm.auto import tqdm


def _to_date(d: Union[str, date]) -> date:
    if isinstance(d, date):
        return d
    return datetime.strptime(d, "%Y-%m-%d").date()


def _season_for_date(d: date) -> str:
    if d.month >= 10:
        end_yy = (d.year + 1) % 100
        return f"{d.year}-{end_yy:02d}"
    else:
        start = d.year - 1
        end_yy = d.year % 100
        return f"{start}-{end_yy:02d}"


def _seasons_between(start: date, end: date) -> List[str]:
    s0 = _season_for_date(start)
    s1 = _season_for_date(end)
    start_year = int(s0.split("-")[0])
    start_year = int(s0.split("-")[0])
    end_year = int(s1.split("-")[0])
    return [f"{y}-{(y + 1) % 100:02d}" for y in range(start_year, end_year + 1)]


async def _fetch_leaguegamelog_df(
    season: str, league_id: str = "00", timeout: int = 60, retries: int = 3
) -> pd.DataFrame:
    def _call() -> pd.DataFrame:
        return leaguegamelog.LeagueGameLog(
            season=season, league_id=league_id, timeout=timeout
        ).get_data_frames()[0]

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return await asyncio.to_thread(_call)
        except Exception as e:
            last_exc = e
            await asyncio.sleep(1.5 * (2**attempt))
    assert last_exc is not None
    raise last_exc


async def _ensure_compound_index(collection) -> None:
    info = await collection.index_information()
    for name, spec in info.items():
        if spec.get("key") == [("game_id", 1)] and spec.get("unique"):
            await collection.drop_index(name)
            break
    await collection.create_index([("game_id", 1), ("team_id", 1)], unique=True)


async def sync_games(
    db,
    start_date: Union[str, date],
    end_date: Union[str, date],
    league_id: str = "00",
    show_progress: bool = False,
) -> int:
    """
    Sync team game logs using nba_api.leaguegamelog for seasons covering [start_date, end_date].
    Inserts only missing docs, uniquely keyed by (game_id, team_id). Returns number inserted.
    """
    start = _to_date(start_date)
    end = _to_date(end_date)
    if end < start:
        return 0

    collection = db["games"]
    await _ensure_compound_index(collection)

    seasons = _seasons_between(start, end)
    all_docs: List[Dict[str, Any]] = []
    seen_keys: set[Tuple[str, int]] = set()

    for season in tqdm(seasons, disable=not show_progress, desc="Seasons"):
        df = await _fetch_leaguegamelog_df(season, league_id=league_id)
        if df is None or df.empty:
            continue

        df["GAME_DATE_PARSED"] = pd.to_datetime(df["GAME_DATE"]).dt.date
        df = df[(df["GAME_DATE_PARSED"] >= start) & (df["GAME_DATE_PARSED"] <= end)]
        if df.empty:
            continue

        for _, row in df.iterrows():
            gid = str(row["GAME_ID"])
            tid = int(row["TEAM_ID"])
            key = (gid, tid)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            game_date = row["GAME_DATE_PARSED"]
            pts = row.get("PTS")
            plus_minus = row.get("PLUS_MINUS")

            all_docs.append(
                {
                    "game_id": gid,
                    "team_id": tid,
                    "season": season,
                    "game_date": game_date.isoformat(),
                    "result": row.get("WL"),
                    "points": int(pts) if pd.notna(pts) else None,
                    "plus_minus": int(plus_minus) if pd.notna(plus_minus) else None,
                }
            )

    if not all_docs:
        return 0

    game_ids = list({doc["game_id"] for doc in all_docs})
    existing = await collection.find(
        {"game_id": {"$in": game_ids}}, {"game_id": 1, "team_id": 1, "_id": 0}
    ).to_list(None)
    existing_keys = {(e["game_id"], int(e["team_id"])) for e in existing}

    docs_to_insert = [
        d for d in all_docs if (d["game_id"], int(d["team_id"])) not in existing_keys
    ]
    if not docs_to_insert:
        return 0

    try:
        result = await collection.insert_many(docs_to_insert, ordered=False)
        return len(result.inserted_ids)
    except BulkWriteError:
        return len(docs_to_insert)
