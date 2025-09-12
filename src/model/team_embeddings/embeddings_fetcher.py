class EmbeddingFetcher:
    def __init__(self, home_embeddings, away_embeddings):
        self.home_embeddings = home_embeddings
        self.away_embeddings = away_embeddings

    def get_home_embedding(self, team_id):
        return self.home_embeddings[team_id]

    def get_away_embedding(self, team_id):
        return self.away_embeddings[team_id]

    def get_all_home_embeddings(self):
        return self.home_embeddings

    def get_all_away_embeddings(self):
        return self.away_embeddings
