import json
import os
import random
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from concurrent.futures import as_completed
from pathlib import Path
from threading import Event, Lock

import numpy as np
import pandas as pd
from tqdm import tqdm

from ..endpoints import BoxScoreAdvanced
from .data_processing import DataProcessing
from .league_game_log import LeagueGameLogProcessing


class BoxScoreAdvancedProcessing(DataProcessing):
    """
    Advanced box score data processing with concurrent workers and persistent caching.

    Due to the large number of requests required to fetch NBA API data (potentially 1000+ games per season),
    this implementation includes several optimizations:

    - Persistent file-based caching to avoid re-fetching already processed games
    - Concurrent processing with multiple workers (ThreadPoolExecutor) for faster data retrieval
    - Rate limiting with random delays and exponential backoff to respect NBA API limits
    - User-Agent rotation to avoid detection as automated scraper
    - Graceful shutdown handling (Ctrl+C) that saves progress before exiting
    - Batch processing with automatic cache saves to prevent data loss
    - Error handling and retry logic for unstable network conditions

    The cache is stored in a separate 'cache/' directory and persists between runs,
    allowing for resumable data collection sessions.
    """

    OBLIGATORY_COLUMNS = None

    def __init__(self, **kwargs):
        if "starting_year" not in kwargs or "ending_year" not in kwargs:
            raise ValueError("Both starting_year and ending_year must be provided")

        self.__starting_year = int(kwargs["starting_year"])
        self.__ending_year = int(kwargs["ending_year"])

        self.__cache_dir = Path(__file__).parent.parent.parent / "cache"
        self.__cache_dir.mkdir(exist_ok=True)

        self.__cache_file = (
            self.__cache_dir
            / f"boxscore_{self.__starting_year}_{self.__ending_year}.json"
        )
        self.__lock = Lock()
        self.__cache = {}
        self.__load_cache()
        self.__stop_event = Event()

        self.__user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]
        signal.signal(signal.SIGINT, self.__signal_handler)
        super().__init__()

    def __process_data__(self):
        data = self.__process_seasons(self.__starting_year, self.__ending_year)
        return self.__convert_numpy_types(data)

    def __signal_handler(self, signum, frame):
        print("\n🛑 Received interrupt signal. Saving cache and stopping...")
        self.__stop_event.set()
        self.__save_cache()
        print("💾 Cache saved. Exiting gracefully.")
        sys.exit(0)

    def __process_seasons(self, starting_year: int, ending_year: int):
        all_games = []
        processing = LeagueGameLogProcessing(
            starting_year=starting_year, ending_year=ending_year, all=True
        )
        processing_data = processing.get_json()
        df = pd.DataFrame(processing_data)
        df = df[["game_id", "date", "home_team_id", "away_team_id"]]

        game_date_map = df.set_index("game_id")["date"].to_dict()
        game_home_team_map = df.set_index("game_id")["home_team_id"].to_dict()
        game_away_team_map = df.set_index("game_id")["away_team_id"].to_dict()

        games = df["game_id"].unique().tolist()

        games_to_process = [g for g in games if g not in self.__cache]
        print(
            f"🔄 Total games: {len(games)}, Cached: {len(games) - len(games_to_process)}, To process: {len(games_to_process)}"
        )

        if games_to_process:
            self.__process_games_parallel(games_to_process)

        for game_id in games:
            if game_id in self.__cache and self.__cache[game_id]:
                game_record = self.__cache[game_id][0].copy()
                game_record["date"] = game_date_map.get(game_id)
                game_record["home_team_id"] = game_home_team_map.get(game_id)
                game_record["away_team_id"] = game_away_team_map.get(game_id)
                all_games.append(game_record)

        all_games.sort(key=lambda x: x.get("date", ""))
        return all_games

    def __process_games_parallel(self, games_to_process):
        max_workers = 4
        batch_size = 15

        print(f"🚀 Starting {max_workers} workers for {len(games_to_process)} games...")

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                processed_count = 0
                errors_count = 0

                with tqdm(
                    total=len(games_to_process), desc="Processing games", ncols=120
                ) as pbar:

                    for i in range(0, len(games_to_process), batch_size):
                        if self.__stop_event.is_set():
                            print(
                                f"\n🛑 Stopping requested. Processed {processed_count} games so far."
                            )
                            break

                        batch = games_to_process[i : i + batch_size]

                        future_to_game = {
                            executor.submit(
                                self.__process_single_game_safe, game_id
                            ): game_id
                            for game_id in batch
                        }

                        for future in as_completed(future_to_game, timeout=60):
                            if self.__stop_event.is_set():
                                break

                            game_id = future_to_game[future]

                            try:
                                result = future.result(timeout=30)
                                if result:
                                    with self.__lock:
                                        self.__cache[game_id] = result
                                else:
                                    errors_count += 1

                                processed_count += 1
                                pbar.update(1)

                                success_rate = (
                                    (
                                        (processed_count - errors_count)
                                        / processed_count
                                        * 100
                                    )
                                    if processed_count > 0
                                    else 0
                                )
                                pbar.set_postfix(
                                    {
                                        "Cached": len(self.__cache),
                                        "Errors": errors_count,
                                        "Success": f"{success_rate:.1f}%",
                                    }
                                )

                            except Exception as e:

                                # Only handle specific exceptions related to futures
                                if isinstance(e, FuturesTimeoutError):
                                    print(f"⏰ TimeoutError for {game_id}: {e}")
                                else:
                                    print(f"⏰ Error for {game_id}: {e}")
                                errors_count += 1
                                processed_count += 1
                                pbar.update(1)

                        self.__save_cache()

                        if not self.__stop_event.is_set() and i + batch_size < len(
                            games_to_process
                        ):
                            pbar.set_description("😴 Rate limit break...")
                            for _ in range(15):
                                if self.__stop_event.is_set():
                                    break
                                time.sleep(1)
                            pbar.set_description("Processing games")

        except KeyboardInterrupt:
            print("\n🛑 KeyboardInterrupt caught. Saving progress...")
            self.__save_cache()
            raise

    def __process_single_game_safe(self, game_id: str):
        delay = random.uniform(0.4, 0.8)
        time.sleep(delay)

        headers = {"User-Agent": random.choice(self.__user_agents)}

        max_retries = 8
        for attempt in range(max_retries):
            try:
                endpoint = BoxScoreAdvanced(game_id=game_id, user_agent=headers)
                dataset = endpoint.get_json()
                data = dataset[-1]

                flattened_data = {
                    "game_id": data["gameId"],
                    "home_team_id": data["homeTeamId"],
                    "away_team_id": data["awayTeamId"],
                }

                home_stats = data["homeTeam"]
                for key, value in home_stats.items():
                    short_key = self.__shorten_key(key)
                    flattened_data[f"home_{short_key}"] = value

                away_stats = data["awayTeam"]
                for key, value in away_stats.items():
                    short_key = self.__shorten_key(key)
                    flattened_data[f"away_{short_key}"] = value

                return [flattened_data]

            except (KeyError, IndexError, TypeError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Final error for game {game_id}: {e}")
                    return None
            except Exception as e:
                # For unexpected errors, print and break
                print(f"❌ Unexpected error for game {game_id}: {e}")
                return None

        return None

    def __load_cache(self):
        if os.path.exists(self.__cache_file):
            try:
                with open(self.__cache_file, "r", encoding="utf-8") as f:
                    self.__cache = json.load(f)
                print(f"✅ Loaded {len(self.__cache)} games from cache file")
            except Exception as e:
                print(f"❌ Error loading cache: {e}")
                self.__cache = {}

    def __save_cache(self):
        try:
            with self.__lock:
                with open(self.__cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.__cache, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving cache: {e}")

    def get_cache_stats(self):
        """
        Returns statistics about the cache file and its contents.

        Returns:
            dict: A dictionary containing:
                - 'cache_file' (str): Path to the cache file.
                - 'cached_games' (int): Number of cached games.
                - 'cache_exists' (bool): Whether the cache file exists.
                - 'cache_size_mb' (float): Size of the cache file in megabytes.
        """
        return {
            "cache_file": str(self.__cache_file),
            "cached_games": len(self.__cache),
            "cache_exists": self.__cache_file.exists(),
            "cache_size_mb": (
                self.__cache_file.stat().st_size / (1024 * 1024)
                if self.__cache_file.exists()
                else 0
            ),
        }

    def __convert_numpy_types(self, data):
        if isinstance(data, list):
            return [self.__convert_numpy_types(item) for item in data]
        elif isinstance(data, dict):
            return {
                key: self.__convert_numpy_types(value) for key, value in data.items()
            }
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif pd.isna(data):
            return None
        return data

    def __shorten_key(self, key: str) -> str:
        key_mappings = {
            "offensiveRating": "off_rating",
            "defensiveRating": "def_rating",
            "estimatedOffensiveRating": "est_off_rating",
            "estimatedDefensiveRating": "est_def_rating",
            "netRating": "net_rating",
            "estimatedNetRating": "est_net_rating",
            "assistPercentage": "ast_pct",
            "assistToTurnover": "ast_to",
            "assistRatio": "ast_ratio",
            "offensiveReboundPercentage": "oreb_pct",
            "defensiveReboundPercentage": "dreb_pct",
            "reboundPercentage": "reb_pct",
            "turnoverRatio": "tov_ratio",
            "effectiveFieldGoalPercentage": "efg_pct",
            "trueShootingPercentage": "ts_pct",
            "usagePercentage": "usg_pct",
            "estimatedUsagePercentage": "est_usg_pct",
            "estimatedPace": "est_pace",
            "pacePer40": "pace_per40",
            "estimatedTeamTurnoverPercentage": "est_tov_pct",
        }
        return key_mappings.get(key, key.lower())
