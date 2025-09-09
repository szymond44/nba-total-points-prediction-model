from torch.utils.data import Dataset
import torch
class NBAEmbeddingDataset(Dataset):
    def __init__(self, X_numeric, X_team_ids, y):
        self.X_numeric = torch.tensor(X_numeric, dtype=torch.float32)
        self.X_team_ids = torch.tensor(X_team_ids, dtype=torch.long)
        self.y = torch.tensor(y, dtype=torch.float32)
    def __len__(self):
        return len(self.y)
    def __getitem__(self, idx):
        return self.X_numeric[idx], self.X_team_ids[idx], self.y[idx]