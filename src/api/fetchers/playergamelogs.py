import asyncio
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Tuple, Union

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog
from pymongo import UpdateOne
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
    end_year = int(s1.split("-")[0])
    return [f"{y}-{(y + 1) % 100:02d}" for y in range(start_year, end_year + 1)]


async def _fetch_leaguegamelog_df(
    season: str, league_id: str = "00", timeout: int = 60, retries: int = 3, p_or_t: str = "P"
) -> pd.DataFrame:
    def _call() -> pd.DataFrame:
        return leaguegamelog.LeagueGameLog(
            season=season,
            league_id=league_id,
            player_or_team_abbreviation=p_or_t,
            timeout=timeout,
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


def _chunked(iterable: Iterable[Any], size: int) -> Iterable[List[Any]]:
    chunk: List[Any] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


async def _ensure_index(collection, defer: bool) -> None:
    if defer:
        return
    await collection.create_index([("GAME_ID", 1), ("PLAYER_ID", 1)], unique=True)


async def _build_index_after(collection) -> None:
    await collection.create_index([("GAME_ID", 1), ("PLAYER_ID", 1)], unique=True)


def _prepare_df(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    df = df.copy()
    df["GAME_DATE_PARSED"] = pd.to_datetime(df["GAME_DATE"]).dt.date
    df = df[(df["GAME_DATE_PARSED"] >= start) & (df["GAME_DATE_PARSED"] <= end)]
    if df.empty:
        return df
    # Ujednolicenie typów kluczy
    df["GAME_ID"] = df["GAME_ID"].astype(str)
    df["PLAYER_ID"] = df["PLAYER_ID"].astype(int)
    return df


async def sync_player_gamelogs(
    db,
    start_date: Union[str, date],
    end_date: Union[str, date],
    league_id: str = "00",
    show_progress: bool = False,
    fast_first_run: bool = True,
    chunk_size: int = 5000,
) -> int:
    """
    Sync player game logs using nba_api.leaguegamelog for seasons covering [start_date, end_date].
    """
    start = _to_date(start_date)
    end = _to_date(end_date)
    if end < start:
        return 0

    collection = db["player_game_logs"]
    is_empty = (await collection.estimated_document_count()) == 0

    await _ensure_index(collection, defer=(fast_first_run and is_empty))

    seasons = _seasons_between(start, end)

    inserted = 0

    if fast_first_run and is_empty:
        frames: List[pd.DataFrame] = []
        for season in tqdm(seasons, disable=not show_progress, desc="Seasons (first run)"):
            df = await _fetch_leaguegamelog_df(season, league_id=league_id, p_or_t="P")
            if df is None or df.empty:
                continue
            df = _prepare_df(df, start, end)
            if df.empty:
                continue
            frames.append(df)

        if not frames:
            return 0

        big = pd.concat(frames, ignore_index=True)
        big = big.drop_duplicates(subset=["GAME_ID", "PLAYER_ID"], keep="last")

        docs = big.drop(columns=["GAME_DATE_PARSED"]).to_dict(orient="records")

        for chunk in tqdm(_chunked(docs, chunk_size), total=(len(docs) + chunk_size - 1) // chunk_size,
                          disable=not show_progress, desc="Inserting"):
            result = await collection.insert_many(chunk, ordered=False)
            inserted += len(result.inserted_ids)

        await _build_index_after(collection)
        return inserted

    for season in tqdm(seasons, disable=not show_progress, desc="Seasons"):
        df = await _fetch_leaguegamelog_df(season, league_id=league_id, p_or_t="P")
        if df is None or df.empty:
            continue
        df = _prepare_df(df, start, end)
        if df.empty:
            continue

        df = df.drop(columns=["GAME_DATE_PARSED"])
        records = df.to_dict(orient="records")

        ops = [
            UpdateOne(
                {"GAME_ID": str(r["GAME_ID"]), "PLAYER_ID": int(r["PLAYER_ID"])},
                {"$setOnInsert": r},
                upsert=True,
            )
            for r in records
        ]

        if not ops:
            continue

        for chunk in _chunked(ops, chunk_size):
            try:
                result = await collection.bulk_write(chunk, ordered=False)
                inserted += (result.upserted_count or 0)
            except BulkWriteError as e:
                details = e.details or {}
                inserted += len(details.get("upserts", []))

    return inserted