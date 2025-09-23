from datetime import date
from typing import Callable, Dict, Literal, Tuple

import pandas as pd
from sklearn.preprocessing import StandardScaler

from data.api_fetcher import ApiFetcher
from data.time_series_dataset import TimeSeriesDataset

EndpointName = Literal["leaguegamelog", "boxscoreadvanced", "mixed"]


class DataPreparation:
    """Class for preparing data for modeling."""

    TRAIN_SIZE = 0.7
    VAL_SIZE = 0.15

    def __init__(self, endpoint: EndpointName, starting_year: int = 2000, ending_year: int = date.today().year):
        self._api = ApiFetcher(starting_year=starting_year, ending_year=ending_year)

        self._endpoint_funcs: Dict[
            str, Callable[..., Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
        ] = {
            "leaguegamelog": self.fetch_league_game_log,
            "boxscoreadvanced": self.fetch_boxscore_advanced,
            "mixed": self.fetch_merged_data,
        }

        if endpoint not in self._endpoint_funcs:
            raise ValueError(f"Unsupported endpoint: {endpoint}")

        self._endpoint = endpoint
        self.dfs: Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] = (None, None, None)
        self.data: Tuple[TimeSeriesDataset, TimeSeriesDataset, TimeSeriesDataset] = (
            self._endpoint_funcs[endpoint]()
        )

    def fetch_league_game_log(self):
        """Fetch and prepare league game log data."""
        df = self._api.get_dataframe(endpoint="leaguegamelog")
        df = df.drop(columns=["game_id"])
        train_df, val_df, test_df = self._split_df(df)
        self.dfs = (train_df, val_df, test_df)

        return self._scale_data(train_df, val_df, test_df)

    def fetch_boxscore_advanced(self):
        """Fetch and prepare boxscore advanced data."""
        df = self._api.get_dataframe(endpoint="boxscoreadvanced")
        df = df.drop(columns=["home_minutes", "away_minutes"])
        drop_cols = [
            "away_est_def_rating",
            "away_est_off_rating",
            "away_est_net_rating",
            "away_pace",
            "away_pie",
            "away_oreb_pct",
            "away_dreb_pct",
            "away_reb_pct",
            "away_ts_pct",
            "home_ts_pct",
        ]
        df = df.drop(columns=drop_cols)
        suffixes = [c.replace("away_", "").replace("home_", "") for c in drop_cols]
        df = df.rename(
            columns={
                c: c.replace("away_", "").replace("home_", "")
                for c in df.columns
                if any(c.endswith(suf) for suf in suffixes)
            }
        )

        additional_cols_to_drop = ['home_usg_pct', 'away_usg_pct']
        df = df.drop(columns=additional_cols_to_drop)

        drop_features = [
            "away_def_rating",
            "away_off_rating",
            "away_net_rating",
            "est_pace",
            "away_pace_per40",
            "home_est_tov_pct",
            "away_est_tov_pct",
            "away_possessions",
            "est_net_rating",
            "est_def_rating",
            "est_off_rating",
            "pie",
            "home_off_rating",
            "home_pace_per40",
            "home_def_rating",
            "home_possessions",
        ]
        df = df.drop(columns=drop_features)

        df_leaguegamelog = self._api.get_dataframe(endpoint="leaguegamelog")
        df_leaguegamelog = df_leaguegamelog[["game_id", "home_pts", "away_pts"]]

        df = df.merge(df_leaguegamelog, on="game_id", how="left")
        df = df.drop(columns=["game_id"])

        train_df, val_df, test_df = self._split_df(df)
        self.dfs = (train_df, val_df, test_df)

        return self._scale_data(train_df, val_df, test_df)

    def fetch_merged_data(self):
        """Fetch and prepare merged data from both endpoints."""
        df1 = self._api.get_dataframe(endpoint="leaguegamelog")
        df2 = self._api.get_dataframe(endpoint="boxscoreadvanced")

        df = df1.merge(df2, on="game_id", suffixes=("_lg", "_ba"))
        df = df.drop(columns=["game_id", "home_minutes", "away_minutes"])
        keep_suffix = "_lg"
        cols_to_keep = []
        for col in df.columns:
            if col.endswith(keep_suffix):
                cols_to_keep.append(col)
            elif not (col.endswith("_lg") or col.endswith("_ba")):
                cols_to_keep.append(col)

        df = df[cols_to_keep]
        df.columns = [col.replace("_lg", "").replace("_ba", "") for col in df.columns]

        drop_cols = [
            "away_est_def_rating",
            "away_est_off_rating",
            "away_est_net_rating",
            "away_pace",
            "away_pie",
            "away_oreb_pct",
            "away_dreb_pct",
            "away_reb_pct",
            "away_ts_pct",
            "home_ts_pct",
        ]
        df = df.drop(columns=drop_cols)
        suffixes = [c.replace("away_", "").replace("home_", "") for c in drop_cols]
        df = df.rename(
            columns={
                c: c.replace("away_", "").replace("home_", "")
                for c in df.columns
                if any(c.endswith(suf) for suf in suffixes)
            }
        )

        df = df.drop(columns=['away_def_rating'])

        train_df, val_df, test_df = self._split_df(df)

        self.dfs = (train_df, val_df, test_df)

        return self._scale_data(train_df, val_df, test_df)

    def _split_df(
        self, data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split dataframe into train, validation and test sets."""
        df = data.copy()
        df = df.sort_values(by="date").reset_index(drop=True)

        n = len(df)
        t_end = int(self.TRAIN_SIZE * n)
        val_end = t_end + int(self.VAL_SIZE * n)

        train = df.iloc[:t_end].copy()
        val = df.iloc[t_end:val_end].copy()
        test = df.iloc[val_end:].copy()

        return train, val, test

    def _scale_data(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
    ) -> Tuple[TimeSeriesDataset, TimeSeriesDataset, TimeSeriesDataset]:
        scaler = StandardScaler()
        labels_cols = ["home_pts", "away_pts", "home_team_id", "away_team_id", "date"]
        feature_cols = [col for col in train_df.columns if col not in labels_cols]
        train_df[feature_cols] = scaler.fit_transform(train_df[feature_cols])
        val_df[feature_cols] = scaler.transform(val_df[feature_cols])
        test_df[feature_cols] = scaler.transform(test_df[feature_cols])
        train_df = train_df.drop(columns=["date"])
        val_df = val_df.drop(columns=["date"])
        test_df = test_df.drop(columns=["date"])

        seq_length = 5
        horizon = 1

        train_dataset = TimeSeriesDataset(
            train_df, sequence_length=seq_length, horizon=horizon
        )
        val_dataset = TimeSeriesDataset(
            val_df, sequence_length=seq_length, horizon=horizon
        )
        test_dataset = TimeSeriesDataset(
            test_df, sequence_length=seq_length, horizon=horizon
        )
        return train_dataset, val_dataset, test_dataset
