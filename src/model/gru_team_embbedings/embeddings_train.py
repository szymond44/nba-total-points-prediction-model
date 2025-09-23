from typing import Tuple, Union

import torch
from torch import nn, optim


class EmbeddingsTrain:
    def __init__(
        self,
        model: nn.Module,
        *,
        learning_rate: float = 1e-3,
        weight_decay: float = 0.0,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: nn.Module = model.to(self.device)
        self.criterion = nn.HuberLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    def _forward(
        self, 
        batch: Union[Tuple[torch.Tensor, torch.Tensor], Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # Poprawka: obsługa sekwencji [batch, seq_len, features] oraz targetu [batch, output_dim]
        if len(batch) == 2:
            xb, yb = batch
            xb, yb = xb.to(self.device), yb.to(self.device)
            # Jeśli xb ma kształt [seq_len, features], dodaj batch dim
            if xb.ndim == 2:
                xb = xb.unsqueeze(0)
            # Jeśli yb ma kształt [output_dim], dodaj batch dim
            if yb.ndim == 1:
                yb = yb.unsqueeze(0)
            preds = self.model(xb)
            return preds, yb
        elif len(batch) == 4:
            xb, home_ids, away_ids, yb = batch
            xb = xb.to(self.device)
            home_ids = home_ids.to(self.device)
            away_ids = away_ids.to(self.device)
            yb = yb.to(self.device)
            # Jeśli xb ma kształt [seq_len, features], dodaj batch dim
            if xb.ndim == 2:
                xb = xb.unsqueeze(0)
            # Jeśli yb ma kształt [output_dim], dodaj batch dim
            if yb.ndim == 1:
                yb = yb.unsqueeze(0)
            preds = self.model(xb, home_ids, away_ids)
            return preds, yb
        else:
            raise ValueError(f"Unexpected batch length: {len(batch)}")

    def step(self, batch) -> float:
        """Update model on a single batch (online step). Returns loss."""
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        preds, yb = self._forward(batch)
        loss_val = self.criterion(preds, yb)
        loss_val.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()
        return loss_val.item()

    def predict(self, batch) -> torch.Tensor:
        """Inference only (no gradient)."""
        self.model.eval()
        with torch.no_grad():
            preds, _ = self._forward(batch)
        return preds