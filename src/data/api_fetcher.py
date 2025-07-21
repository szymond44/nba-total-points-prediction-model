from nba_api.stats.static import teams

class ApiFetcher:
    def __init__(self):
        self.teams = teams.get_teams()