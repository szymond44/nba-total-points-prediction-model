import torch
from torch.utils.data import Dataset


class TimeSeriesDataset(Dataset):
    """Custom Dataset for time series data."""

    LABELS = ["home_pts", "away_pts"]

    def __init__(self, data, sequence_length, horizon):
        self.seq_length = sequence_length
        self.horizon = horizon
        self.features = data.drop(columns=self.LABELS).values.astype("float32")
        self.labels = data[self.LABELS].values.astype("float32")

    def __getitem__(self, index):
        features = self.features[index : index + self.seq_length]
        label = self.labels[
            index + self.seq_length : index + self.seq_length + self.horizon
        ]
        return torch.from_numpy(features), torch.from_numpy(label)

    def __len__(self):
        return len(self.features) - self.seq_length - self.horizon + 1
