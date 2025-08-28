import torch
import torch.nn as nn

class TeamEmbeddings(nn.Module):
    def __init__(self, num_teams, embedding_dim=8, num_features=22):
        super().__init__()
        self.embedding = nn.Embedding(num_teams, embedding_dim)
        nn.init.normal_(self.embedding.weight, mean=0.0, std=0.1)

        self.feature_net = nn.Sequential(
            nn.Linear(num_features, 16),
            nn.ReLU(),
            #nn.Dropout(0.4),
            nn.Linear(16, 8),
        )
        combined_size = embedding_dim * 2 + 8
        self.final_net = nn.Sequential(
            nn.Linear(combined_size, 8),
            nn.ReLU(),
            #nn.Dropout(0.4),
            nn.Linear(8, 1),
        )
    
    def forward(self, home_team_id, away_team_id, game_features):
        home_embed = self.embedding(home_team_id)
        away_embed = self.embedding(away_team_id)
        
        # Przetwórz statystyki meczu
        feature_out = self.feature_net(game_features)
        
        # Połącz wszystko
        combined = torch.cat([home_embed, away_embed, feature_out], dim=-1)
        
        # Final prediction
        points = self.final_net(combined)
        return points
