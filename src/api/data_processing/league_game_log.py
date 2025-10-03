import pandas as pd

from ..api_config import ApiConfig
from ..endpoints import LeagueGameLog
from .data_processing import DataProcessing


class LeagueGameLogProcessing(DataProcessing):
    """Class for processing league game log data from the API."""

    OBLIGATORY_COLUMNS = [
    "game_id",
    "home_fga",
    "away_fga",
    "home_fg_pct",
    "away_fg_pct",
    "home_fg3a",
    "away_fg3a",
    "home_fg3_pct",
    "away_fg3_pct",
    "home_fta",     
    "away_fta",     
    "home_ft_pct",   
    "away_ft_pct",   
    "home_ftm",      
    "away_ftm",      
    "home_oreb",
    "away_oreb",
    "home_dreb",
    "away_dreb",
    "home_ast",
    "away_ast",
    "home_stl",
    "away_stl",
    "home_blk",
    "away_blk",
    "home_tov",
    "away_tov",
    "home_pf",
    "away_pf",
    "home_pts",
    "away_pts",
    "home_team_id",
    "away_team_id",
    "date",
]
    

    def __init__(self, **kwargs):
        if "starting_year" not in kwargs or "ending_year" not in kwargs:
            raise ValueError("Both starting_year and ending_year must be provided")

        self.__all__ = kwargs.get("all", False)

        self.__starting_year__ = int(kwargs["starting_year"])
        self.__ending_year__ = int(kwargs["ending_year"])
        super().__init__(**kwargs)

    def __process_data__(self):
        all_games = []
        for season in self.__calculate_season_list__(
            self.__starting_year__, self.__ending_year__
        ):
            season_data = self.__process_single_season__(season)
            all_games.extend(season_data)

        df = pd.DataFrame(all_games)
        df = self.__get_id__(df.copy())
        df = self.__apply_params__(df.copy())
        df = df.sort_values(by="date").reset_index(drop=True)
        return df.to_dict(orient="records")

    def __get_id__(self, dataframe: pd.DataFrame):
        df = dataframe.copy()
        teams_sorted = sorted(df["home_team"].unique())
        team_to_id = {team: idx for idx, team in enumerate(teams_sorted)}

        df["home_team_id"] = df["home_team"].map(team_to_id)
        df["away_team_id"] = df["away_team"].map(team_to_id)

        return df

    def __apply_params__(self, df):
        if hasattr(self, "__all__") and self.__all__:
            return df
        return df[self.OBLIGATORY_COLUMNS]

    def __process_single_season__(self, season: str):
        endpoint = LeagueGameLog(season=season)
        df = endpoint.get_dataframe()

        games_dict = {}

        for _, row in df.iterrows():
            game_id = row["GAME_ID"]
            game_date = row["GAME_DATE"]
            team_name = row["TEAM_NAME"]
            matchup = row["MATCHUP"]
            is_home = "vs." in matchup

            if game_id not in games_dict:
                games_dict[game_id] = {
                    "game_id": game_id,
                    "date": game_date,
                    "home_team": None,
                    "away_team": None,
                    "home_stats": {},
                    "away_stats": {},
                }

            stats = {}
            for col in df.columns:
                if col not in ["GAME_ID", "TEAM_NAME", "MATCHUP", "GAME_DATE"]:
                    stats[col] = row[col]

            if is_home:
                games_dict[game_id]["home_team"] = team_name
                games_dict[game_id]["home_stats"] = stats
            else:
                games_dict[game_id]["away_team"] = team_name
                games_dict[game_id]["away_stats"] = stats

        final_games = []
        for game_id, game_info in games_dict.items():
            if (
                game_info["home_team"]
                and game_info["away_team"]
                and game_info["home_stats"]
                and game_info["away_stats"]
            ):
                home_stats = game_info["home_stats"]
                away_stats = game_info["away_stats"]

                game_record = {
                    "game_id": game_id,
                    "date": game_info["date"],
                    "home_team": game_info["home_team"],
                    "away_team": game_info["away_team"],
                }

                for stat, value in home_stats.items():
                    game_record[f"home_{stat.lower()}"] = value

                for stat, value in away_stats.items():
                    game_record[f"away_{stat.lower()}"] = value

                final_games.append(game_record)

        df = pd.DataFrame(final_games)
        df = df.sort_values("date").reset_index(drop=True)

        return df.to_dict(orient="records")

    def __calculate_season_list__(self, starting_year, ending_year):
        starting_year = max(starting_year, ApiConfig.MINIMAL_YEAR)
        ending_year = min(ending_year, ApiConfig.MAXIMAL_YEAR)
        seasons = []
        for year in range(starting_year, ending_year):
            season_str = f"{year}-{str(year + 1)[-2:]}"
            seasons.append(season_str)
        return seasons
