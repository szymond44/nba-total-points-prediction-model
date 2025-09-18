from datetime import date
from typing import Callable, Dict, Literal, Tuple

import pandas as pd
from sklearn.preprocessing import StandardScaler

from data.api_fetcher import ApiFetcher
from data.time_series_dataset import TimeSeriesDataset

EndpointName = Literal["leaguegamelog", "boxscoreadvanced"]


class DataPreparation:
    """Class for preparing data for modeling."""

    STARTING_YEAR = date.today().year - 6
    ENDING_YEAR = date.today().year + 1

    TRAIN_SIZE = 0.7
    VAL_SIZE = 0.15

    def __init__(self, endpoint: EndpointName):
        self._api = ApiFetcher(starting_year=2019, ending_year=2025)

        self._endpoint_funcs: Dict[
            str, Callable[..., Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
        ] = {
            "leaguegamelog": self.fetch_league_game_log,
            "boxscoreadvanced": self.fetch_boxscore_advanced,
        }

        if endpoint not in self._endpoint_funcs:
            raise ValueError(f"Unsupported endpoint: {endpoint}")

        self._endpoint = endpoint
        self.data: Tuple[TimeSeriesDataset, TimeSeriesDataset, TimeSeriesDataset] = (
            self._endpoint_funcs[endpoint]()
        )

    def fetch_league_game_log(self):
        """Fetch and prepare league game log data."""
        df = self._api.get_dataframe(endpoint="leaguegamelog")
        df = df.drop(columns=["game_id"])
        train_df, val_df, test_df = self._split_df(df)

        return self._scale_data(
            train_df, val_df, test_df)

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
        df = df.rename(
            columns={c: c.replace("away_", "").replace("home_", "") for c in drop_cols}
        )

        df_leaguegamelog = self._api.get_dataframe(endpoint="leaguegamelog")
        df_leaguegamelog = df_leaguegamelog[["game_id", "home_pts", "away_pts"]]

        df = df.merge(df_leaguegamelog, on="game_id", how="left")
        df = df.drop(columns=["game_id"])

        train_df, val_df, test_df = self._split_df(df)


        return self._scale_data(
            train_df, val_df, test_df)

    def _split_df(
        self, data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split dataframe into train, validation and test sets."""
        df = data.copy()
        df = df.sort_values(by="date")
        df = df.drop(columns=["date"])

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
        labels_cols = ["home_pts", "away_pts"]
        feature_cols = [col for col in train_df.columns if col not in labels_cols]
        train_df[feature_cols] = scaler.fit_transform(train_df[feature_cols])
        val_df[feature_cols] = scaler.transform(val_df[feature_cols])
        test_df[feature_cols] = scaler.transform(test_df[feature_cols])

        seq_length = 10
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
