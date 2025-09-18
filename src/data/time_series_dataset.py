import pandas as pd
import torch
from torch.utils.data import Dataset


class TimeSeriesDataset(Dataset):
    """Custom Dataset for time series data."""

    LABELS = ["home_pts", "away_pts"]

    def __init__(
        self,
        data: pd.DataFrame,
        sequence_length: int,
        horizon: int,
        home_id_col: str = "home_team_id",
        away_id_col: str = "away_team_id",
        id_map: dict[int, int] | None = None,  # nowość: globalna mapa ID -> idx
    ):
        self.seq_length = sequence_length
        self.horizon = horizon

        self._has_ids = home_id_col in data.columns and away_id_col in data.columns
        if self._has_ids:
            if id_map is None:
                # UWAGA: lepiej przekazać id_map z DataPreparation (spójność między splitami)
                uniq = pd.unique(pd.concat([data[home_id_col], data[away_id_col]], ignore_index=True))
                id_map = {int(v): i for i, v in enumerate(sorted(map(int, uniq)))}
            self.id_map = id_map
            self.n_teams = len(self.id_map)

            home_m = data[home_id_col].map(self.id_map)
            away_m = data[away_id_col].map(self.id_map)
            if home_m.isna().any() or away_m.isna().any():
                missing = set(pd.concat([data[home_id_col], data[away_id_col]], ignore_index=True)) - set(self.id_map.keys())
                raise ValueError(f"Unseen team IDs in split: {sorted(map(int, missing))}")

            self.home_ids = home_m.astype("int64").values
            self.away_ids = away_m.astype("int64").values
            drop_cols = self.LABELS + [home_id_col, away_id_col]
        else:
            self.id_map = {}
            self.n_teams = 0
            drop_cols = self.LABELS

        self.features = data.drop(columns=drop_cols, errors="ignore").values.astype("float32")
        self.labels = data[self.LABELS].values.astype("float32")

    def __getitem__(self, index):
        x = self.features[index : index + self.seq_length]
        if self.horizon == 1:
            y = self.labels[index + self.seq_length]  # (2,)
        else:
            y = self.labels[index + self.seq_length : index + self.seq_length + self.horizon]  # (H, 2)

        if self._has_ids:
            home_ids = self.home_ids[index : index + self.seq_length]
            away_ids = self.away_ids[index : index + self.seq_length]
            return torch.from_numpy(x), torch.as_tensor(home_ids, dtype=torch.long), torch.as_tensor(away_ids, dtype=torch.long), torch.from_numpy(y)

        return torch.from_numpy(x), torch.from_numpy(y)

    def __len__(self):
        return len(self.features) - self.seq_length - self.horizon + 1
# ...existing code...