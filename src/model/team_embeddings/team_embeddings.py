import torch
import torch.nn as nn
import torch.nn.functional as F
class TeamEmbeddings(nn.Module):
    def __init__(self, num_teams, embedding_dim, num_numeric_features):
        super(TeamEmbeddings, self).__init__()
        
        # Embedding layers for home and away teams
        self.home_embedding = nn.Embedding(num_teams, embedding_dim)
        self.away_embedding = nn.Embedding(num_teams, embedding_dim)
        
        # Input layer size = numeric features + 2 embeddings concatenated
        input_size = num_numeric_features + embedding_dim * 2
        
        # Hidden layers
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        
        # Output layer (predict home_pts and away_pts)
        self.out = nn.Linear(32, 2)
        
    def forward(self, numeric_features, team_ids):
        
        home_emb = self.home_embedding(team_ids[:, 0])
        away_emb = self.away_embedding(team_ids[:, 1])
        
        # Concatenate embeddings with numeric features
        x = torch.cat([numeric_features, home_emb, away_emb], dim=1)
        
        # Forward pass through hidden layers
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        
        # Output predicted points
        out = self.out(x)
        return out


