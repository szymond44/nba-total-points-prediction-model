import requests
import pandas as pd
import json

response_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Host': 'stats.nba.com',
    'Referer': 'https://www.nba.com/',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true'
}

response_params = {
    'Counter': '10',
    'DateFrom': '',
    'DateTo': '',
    'Direction': 'DESC',
    'LeagueID': '00',
    'PlayerOrTeam': 'T',
    'Season': '2024-25',
    'SeasonType': 'Regular Season',
    'Sorter': 'DATE'
}
class ApiFetcher:
    def __init__(self):
        self.data = self.__fetch_dataframe__()

    def __fetch_dataframe__(self):
        base_url = "https://stats.nba.com/stats/leaguegamelog"
        

        response = requests.get(url=base_url, headers=response_headers, params=response_params)
        data = response.json()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)
        games_dict = {}

        for _, row in df.iterrows():
            game_id = row['GAME_ID']
            game_date = row['GAME_DATE']
            team_name = row['TEAM_NAME']
            matchup = row['MATCHUP']
            is_home = 'vs.' in matchup

            if game_id not in games_dict:
                games_dict[game_id] = {
                    'game_id': game_id,
                    'date': game_date,
                    'home_team': None,
                    'away_team': None,
                    'home_stats': {},
                    'away_stats': {}
                }

            stats = {}
            for col in headers:
                if col not in ['GAME_ID', 'TEAM_NAME', 'MATCHUP', 'GAME_DATE']:
                    stats[col] = row[col]

            if is_home:
                games_dict[game_id]['home_team'] = team_name
                games_dict[game_id]['home_stats'] = stats
            else:
                games_dict[game_id]['away_team'] = team_name
                games_dict[game_id]['away_stats'] = stats

        # Create the final list of games with all stats
        final_games = []
        for game_id, game_info in games_dict.items():
            if game_info['home_team'] and game_info['away_team'] and game_info['home_stats'] and game_info['away_stats']:
                home_stats = game_info['home_stats']
                away_stats = game_info['away_stats']

                game_record = {
                    'game_id': game_id,
                    'date': game_info['date'],
                    'home_team': game_info['home_team'],
                    'away_team': game_info['away_team']
                }

                for stat, value in home_stats.items():
                    game_record[f'home_{stat.lower()}'] = value

                for stat, value in away_stats.items():
                    game_record[f'away_{stat.lower()}'] = value

                final_games.append(game_record)

        games_df = pd.DataFrame(final_games)
        games_df = games_df.sort_values('date').reset_index(drop=True)

        return games_df
    
    def get_numeric_dataframe(self):
        """
        Returns NBA game data structured for machine learning analysis.
        Each row represents a complete game with home/away team statistics
        ready for feature engineering and model training.
        """
        base_columns = ['fga', 'fg_pct', 'fg3a', 'fg3_pct', 'oreb', 'dreb', 'ast', 'stl', 'blk', 'tov', 'pf', 'pts']
        columns = []
        
        for col in base_columns:
            columns.append(f'home_{col}')
            columns.append(f'away_{col}')

        return self.data[columns] 