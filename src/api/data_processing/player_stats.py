import pandas as pd

from ..api_config import ApiConfig
from ..endpoints import PlayerDashboard
from .data_processing import DataProcessing


class PlayerStatsProcessing(DataProcessing):
    """Class for processing player game-by-game statistics data from the API."""

    OBLIGATORY_COLUMNS = [
        "player_id",
        "player_name",
        "team_id",
        "team_abbreviation",
        "game_id",
        "game_date",
        "matchup",
        "wl",
        "min",
        "fgm",
        "fga",
        "fg_pct",
        "fg3m",
        "fg3a",
        "fg3_pct",
        "ftm",
        "fta",
        "ft_pct",
        "oreb",
        "dreb",
        "reb",
        "ast",
        "stl",
        "blk",
        "tov",
        "pf",
        "pts",
        "plus_minus",
        "season",
    ]

    def __init__(self, **kwargs):
        if "starting_year" not in kwargs or "ending_year" not in kwargs:
            raise ValueError("Both starting_year and ending_year must be provided")

        self.__all__ = kwargs.get("all", False)
        self.__season_type__ = kwargs.get("season_type", "Regular Season")
        self.__player_id__ = kwargs.get("player_id", None)
        self.__team_id__ = kwargs.get("team_id", None)
        self.__date_from__ = kwargs.get("date_from", "")
        self.__date_to__ = kwargs.get("date_to", "")
        self.__outcome__ = kwargs.get("outcome", "")
        self.__location__ = kwargs.get("location", "")

        self.__starting_year__ = int(kwargs["starting_year"])
        self.__ending_year__ = int(kwargs["ending_year"])
        super().__init__()

    def __process_data__(self):
        all_games = []
        for season in self.__calculate_season_list__(
            self.__starting_year__, self.__ending_year__
        ):
            season_data = self.__process_single_season__(season)
            all_games.extend(season_data)

        df = pd.DataFrame(all_games)
        
        if not df.empty:
            df = self.__add_derived_features__(df.copy())
            df = self.__apply_params__(df.copy())
            df = df.sort_values(by=["season", "game_date", "player_name"]).reset_index(drop=True)
        
        return df.to_dict(orient="records")

    def __apply_params__(self, df):
        """Apply column filtering based on __all__ parameter."""
        if hasattr(self, "__all__") and self.__all__:
            return df
        
        # Only return columns that exist in the dataframe
        available_columns = [col for col in self.OBLIGATORY_COLUMNS if col in df.columns]
        return df[available_columns]

    def __process_single_season__(self, season: str):
        """Process player game logs for a single season."""
        endpoint = PlayerDashboard(
            season=season,
            season_type=self.__season_type__,
            player_id=self.__player_id__,
            team_id=self.__team_id__,
            date_from=self.__date_from__,
            date_to=self.__date_to__,
            outcome=self.__outcome__,
            location=self.__location__,
        )
        df = endpoint.get_dataframe()

        if df.empty:
            return []

        # Normalize column names to lowercase with underscores
        df.columns = [col.lower() for col in df.columns]
        
        # Add season column
        df["season"] = season

        return df.to_dict(orient="records")

    def __add_derived_features__(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for modeling."""
        if df.empty:
            return df

        # True Shooting Percentage
        if all(col in df.columns for col in ["pts", "fga", "fta"]):
            df["ts_pct"] = df["pts"] / (2 * (df["fga"] + 0.44 * df["fta"]) + 1e-6)

        # Assist to Turnover Ratio
        if "ast" in df.columns and "tov" in df.columns:
            df["ast_to_ratio"] = df["ast"] / (df["tov"] + 1e-6)

        # Points per Field Goal Attempt
        if "pts" in df.columns and "fga" in df.columns:
            df["pts_per_fga"] = df["pts"] / (df["fga"] + 1e-6)

        # Rebounds per Minute
        if "reb" in df.columns and "min" in df.columns:
            df["reb_per_min"] = df["reb"] / (df["min"] + 1e-6)

        # Scoring + Playmaking composite
        if "pts" in df.columns and "ast" in df.columns:
            df["pts_ast_composite"] = df["pts"] + (df["ast"] * 2)

        # Usage composite
        if all(col in df.columns for col in ["fga", "fta", "tov"]):
            df["usage_composite"] = df["fga"] + (df["fta"] * 0.44) + df["tov"]

        # Three-point attempt rate
        if "fg3a" in df.columns and "fga" in df.columns:
            df["fg3a_rate"] = df["fg3a"] / (df["fga"] + 1e-6)

        # Free throw rate
        if "fta" in df.columns and "fga" in df.columns:
            df["fta_rate"] = df["fta"] / (df["fga"] + 1e-6)

        # Game outcome binary
        if "wl" in df.columns:
            df["is_win"] = (df["wl"] == "W").astype(int)

        # Home/Away indicator
        if "matchup" in df.columns:
            df["is_home"] = df["matchup"].str.contains("vs.", case=False, na=False).astype(int)

        return df

    def __calculate_season_list__(self, starting_year, ending_year):
        """Generate list of NBA seasons between starting and ending years."""
        starting_year = max(starting_year, ApiConfig.MINIMAL_YEAR)
        ending_year = min(ending_year, ApiConfig.MAXIMAL_YEAR)
        seasons = []
        for year in range(starting_year, ending_year):
            season_str = f"{year}-{str(year + 1)[-2:]}"
            seasons.append(season_str)
        return seasons