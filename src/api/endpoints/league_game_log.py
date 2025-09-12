from .endpoint import Endpoint

class LeagueGameLog(Endpoint):
    def __init__(self, counter=10, season='2024-25', season_type='Regular Season', sorter='DATE', date_from='', date_to='', league_id='00', player_or_team='T', direction='DESC'):
        params = {
            'Counter': counter,
            'DateFrom': date_from,
            'DateTo': date_to,
            'Direction': direction,
            'LeagueID': league_id,
            'PlayerOrTeam': player_or_team,
            'Season': season,
            'SeasonType': season_type,
            'Sorter': sorter
        }
        super().__init__(endpoint="leaguegamelog", params=params)
    