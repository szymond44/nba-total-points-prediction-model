from sklearn.preprocessing import StandardScaler
from .team_embeddings import TeamEmbeddings
from .embeddings_dataset import NBAEmbeddingDataset
from torch.utils.data import DataLoader
import torch.nn as nn
import torch
import torch.optim as optim
import numpy as np

class TeamEmbeddingsModel:
    OBLIGATORY_COLUMNS = ['home_fga', 'away_fga', 'home_fg_pct', 'away_fg_pct', 'home_fg3a',
       'away_fg3a', 'home_fg3_pct', 'away_fg3_pct', 'home_oreb', 'away_oreb',
       'home_dreb', 'away_dreb', 'home_ast', 'away_ast', 'home_stl',
       'away_stl', 'home_blk', 'away_blk', 'home_tov', 'away_tov', 'home_pf',
       'away_pf', 'home_pts', 'away_pts', 'date',
       'home_team_id', 'away_team_id']
    
    def __init__(self, data):
        self.__validate_data__(data)
        df = data.copy().sort_values(by='date').reset_index(drop=True)
        train_df, val_df, test_df = np.split(
            df, 
            [int(0.7*len(df)), int(0.85*len(df))]
        )
        X_train_num, X_train_ids, y_train, scaler, _ = self.__prepare_df__(train_df)
        X_val_num, X_val_ids, y_val, _, _ = self.__prepare_df__(val_df, scaler=scaler)
        X_test_num, X_test_ids, y_test, _, _ = self.__prepare_df__(test_df, scaler=scaler)

        self.__train_dataset__ = NBAEmbeddingDataset(X_train_num, X_train_ids, y_train)
        self.__val_dataset__ = NBAEmbeddingDataset(X_val_num, X_val_ids, y_val)
        self.__test_dataset__ = NBAEmbeddingDataset(X_test_num, X_test_ids, y_test)

        self.__num_teams__ = df['home_team_id'].nunique()
        self.__embedding_dim__ = 8
        self.__num_numeric_features__ = X_train_num.shape[1]
                                    
    def __validate_data__(self, data):
        for col in self.OBLIGATORY_COLUMNS:
            if col not in data.columns:
                raise ValueError(f"Missing obligatory column: {col}")
        if data['home_team_id'].nunique() != data['away_team_id'].nunique():
            raise ValueError("Number of unique home_team_id and away_team_id must be the same.")
        if data['home_team_id'].nunique() < 30:
            raise ValueError("Number of unique teams must be at least 30.")
    
    def __prepare_df__(self, df1, target_cols=['home_pts', 'away_pts'], scaler=None):
        team_id_cols = ['home_team_id', 'away_team_id']
        exclude_cols = target_cols + team_id_cols + ['date', 'home_team', 'away_team']
        numeric_cols = [col for col in df1.columns if col not in exclude_cols]


        X_numeric_raw = df1[numeric_cols].values
        X_team_ids = df1[team_id_cols].astype(int).values
        y = df1[target_cols].values 
        if scaler is None:
            scaler = StandardScaler()
            X_numeric = scaler.fit_transform(X_numeric_raw)
        else:
            X_numeric = scaler.transform(X_numeric_raw)

        return X_numeric, X_team_ids, y, scaler, numeric_cols

    def train(self):
        train_loader = DataLoader(self.__train_dataset__, batch_size=64, shuffle=True)
        val_loader = DataLoader(self.__val_dataset__, batch_size=64, shuffle=False)
        test_loader = DataLoader(self.__test_dataset__, batch_size=64, shuffle=False)

        model = TeamEmbeddings(self.__num_teams__, self.__embedding_dim__, self.__num_numeric_features__)

        criterion = nn.MSELoss()
        learning_rate = 0.009187
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        num_epochs = 250

        train_losses = []
        val_losses = []

        for epoch in range(num_epochs):
            model.train()
            train_loss_epoch = 0
            for X_num_batch, X_ids_batch, y_batch in train_loader:
                optimizer.zero_grad()
                outputs = model(X_num_batch, X_ids_batch)
                loss = criterion(outputs, y_batch)
                loss.backward()
                optimizer.step()
                train_loss_epoch += loss.item() * X_num_batch.size(0)
            train_loss_epoch /= len(train_loader.dataset)
            train_losses.append(train_loss_epoch)

            model.eval()
            val_loss_epoch = 0
            with torch.no_grad():
                for X_num_batch, X_ids_batch, y_batch in val_loader:
                    outputs = model(X_num_batch, X_ids_batch)
                    loss = criterion(outputs, y_batch)
                    val_loss_epoch += loss.item() * X_num_batch.size(0)
            val_loss_epoch /= len(val_loader.dataset)
            val_losses.append(val_loss_epoch)

        model.eval()
        test_loss = 0
        with torch.no_grad():
            for X_num_batch, X_ids_batch, y_batch in test_loader:
                outputs = model(X_num_batch, X_ids_batch)
                loss = criterion(outputs, y_batch)
                test_loss += loss.item() * X_num_batch.size(0)
        return test_loss / len(test_loader.dataset), model
    
    def train_multiple(self, n=20):
        results = [self.train() for _ in range(n)]
        test_mse = [res[0] for res in results]
        models = [res[1] for res in results]
        return test_mse, models
        

