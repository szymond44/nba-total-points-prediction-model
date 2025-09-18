import torch
from torch import nn


class TeamEmbeddings(nn.Module):
    """
    TeamEmbeddings is a PyTorch module for modeling team-specific embeddings in sequential data, such as sports matches.
    Args:
        input_num_features (int): Number of numerical features per time step.
        n_teams (int): Total number of unique teams.
        emb_dim (int): Dimension of the team embeddings.
        hidden_size (int): Number of features in the GRU hidden state.
        num_layers (int): Number of GRU layers.
        output_size (int, optional): Output size of the final linear layer. Default is 2.
    Attributes:
        home_emb (nn.Embedding): Embedding layer for home teams.
        away_emb (nn.Embedding): Embedding layer for away teams.
        gru (nn.GRU): GRU layer for processing sequential data.
        fc (nn.Linear): Final linear layer for output.
    Forward Args:
        x_num (Tensor): Numerical input features of shape (B, T, F), where B is batch size, T is sequence length, F is number of features.
        home_ids (Tensor): Home team IDs of shape (B,) or (B, T).
        away_ids (Tensor): Away team IDs of shape (B,) or (B, T).
    Returns:
        Tensor: Output predictions of shape (B, output_size).
    Notes:
        - If home_ids and away_ids are provided as (B,), they are expanded to (B, T, E) to match the sequence length.
        - Team embeddings are concatenated with numerical features before passing through the GRU.
        - Only the last time step's output from the GRU is used for prediction.
    """
    def __init__(self, input_num_features: int, n_teams: int, emb_dim: int, hidden_size: int, num_layers: int, output_size: int = 2, dropout: float = 0.2):
        super().__init__()
        self.home_emb = nn.Embedding(n_teams, emb_dim)
        self.away_emb = nn.Embedding(n_teams, emb_dim)
        gru_dropout = dropout if num_layers > 1 else 0.0
        self.gru = nn.GRU(input_num_features + 2 * emb_dim, hidden_size, num_layers, batch_first=True, dropout=gru_dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)
        

    def forward(self, x_num, home_ids=None, away_ids=None):
        B, T, _ = x_num.shape
        if home_ids is not None and away_ids is not None:
            if home_ids.ndim == 1:
                home_ids = home_ids.unsqueeze(1).expand(-1, T)
                away_ids = away_ids.unsqueeze(1).expand(-1, T)
            # walidacja zakresu
            if home_ids.max() >= self.home_emb.num_embeddings or away_ids.max() >= self.away_emb.num_embeddings:
                raise ValueError(f"Team id out of range for embeddings (max_id={int(torch.maximum(home_ids.max(), away_ids.max()))}, num_embeddings={self.home_emb.num_embeddings})")
            he = self.home_emb(home_ids)
            ae = self.away_emb(away_ids)
        else:
            E = self.home_emb.embedding_dim
            he = x_num.new_zeros((B, T, E))
            ae = x_num.new_zeros((B, T, E))
        x = torch.cat([x_num, he, ae], dim=-1)
        x = apply_time_decay(x, decay_factor=0.8)
        out, _ = self.gru(x)
        out = out[:, -1, :]
        self.dropout(out)
        return self.fc(out)
    

def apply_time_decay(x, decay_factor=0.8):
    """
    x: (B, T, F) - batch, sequence_length, features
    decay_factor: float, np. 0.8 → starsze mecze mają 0.8, 0.64, 0.512 ...
    """
    B, T, F = x.shape
    weights = torch.tensor([decay_factor ** (T - 1 - t) for t in range(T)],
                           device=x.device).view(1, T, 1)
    return x * weights