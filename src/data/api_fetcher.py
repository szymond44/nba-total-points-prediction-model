import requests
import pandas as pd
import json
class ApiFetcher:

    RESPONSE_HEADERS = {
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

    BASE_URL = "https://stats.nba.com/stats/leaguegamelog"

    MINIMAL_YEAR = 1980
    MAXIMAL_YEAR = 2050

    NUMERIC_COLUMNS = ['fga', 'fg_pct', 'fg3a', 'fg3_pct', 'oreb', 'dreb', 'ast', 'stl', 'blk', 'tov', 'pf', 'pts']

    def __init__(self, starting_year, ending_year):
        self.__seasons__ = self.__calculate_season_list__(starting_year, ending_year)
        data = self.__fetch_dataframes__()
        self.data = data.dropna(axis=0).sort_values(by='date').reset_index(drop=True)

    def __calculate_season_list__(self, starting_year, ending_year):
        starting_year = max(starting_year, self.MINIMAL_YEAR)
        ending_year = min(ending_year, self.MAXIMAL_YEAR)
        seasons = []
        for year in range(starting_year, ending_year):
            season_str = f"{year}-{str(year + 1)[-2:]}"
            seasons.append(season_str)
        return seasons
    
    
    def __fetch_dataframes__(self):
        data = pd.DataFrame()
        for season in self.__seasons__:
            df = self.__fetch_single_dataframe__(season)
            if not df.empty:
                data = pd.concat([data, df], ignore_index=True)
            else:
                if not data.empty:
                    return data
        return data

    def __fetch_single_dataframe__(self, season: str):

        response_params = {
            'Counter': '10',
            'DateFrom': '',
            'DateTo': '',
            'Direction': 'DESC',
            'LeagueID': '00',
            'PlayerOrTeam': 'T',
            'Season': season,
            'SeasonType': 'Regular Season',
            'Sorter': 'DATE'
        }


        response = requests.get(url=self.BASE_URL, headers=self.RESPONSE_HEADERS, params=response_params)
        data = response.json()

        if response.status_code != 200 or 'resultSets' not in data or not data['resultSets']:
            return pd.DataFrame()

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
    
    def __get_time_feature__(self, df):
        df = df.copy()  # Unikaj modyfikacji oryginalnego DataFrame
        # Convert date to datetime if it's not already
        df['date'] = pd.to_datetime(df['date'])
        # Calculate time coefficient: more recent games get higher weight
        time_diff = (df['date'].max() - df['date']).dt.days
        df['time_coeff'] = 1 / (1 + time_diff)
        df = df.drop(columns=['date'])
        return df
    
    def __get_team_id__(self, df):
        numeric_df = df.copy()
        teams_sorted = sorted(numeric_df['home_team'].unique()) 
        team_to_id = {team: idx for idx, team in enumerate(teams_sorted)} 

        numeric_df['home_team_id'] = self.data['home_team'].map(team_to_id)
        numeric_df['away_team_id'] = self.data['away_team'].map(team_to_id)

        return numeric_df

    def __get_season_id__(self, data):
        
        df = data.copy()
    
        # Ensure 'season' column exists
        if 'season' not in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['season'] = df['date'].apply(lambda d: d.year if d.month >= 10 else d.year - 1)
    
        # Create team-season keys
        df['home_team_season'] = df['home_team'] + "_" + df['season'].astype(str)
        df['away_team_season'] = df['away_team'] + "_" + df['season'].astype(str)
    
        # Map team-season to numeric IDs
        unique_teams = sorted(df['home_team_season'].unique().tolist() + df['away_team_season'].unique().tolist())
        team_season_to_id = {team_season: idx for idx, team_season in enumerate(unique_teams)}
    
        # Assign IDs
        df['home_team_season_id'] = df['home_team_season'].map(team_season_to_id)
        df['away_team_season_id'] = df['away_team_season'].map(team_season_to_id)

        df = df.drop(columns=['season', 'home_team_season', 'away_team_season'])
    
        return df

    
    def get_dataframe(self, numeric: bool = True, ids: bool = False, date: bool = False, time_coeff: bool = False, season_id: bool = False):
        base_columns = self.NUMERIC_COLUMNS if numeric else self.NUMERIC_COLUMNS + ['team']
        columns = []
        """
        Parametrized interface to get the raw dataframe
        """
        for col in base_columns:
            columns.append(f'home_{col}')
            columns.append(f'away_{col}')

        if date or time_coeff or season_id:
            columns += ['date']
        df = self.data[columns].copy()
        if ids:
            df = self.__get_team_id__(df)
        if time_coeff:
            df = self.__get_time_feature__(df)
        if season_id:
            df = self.__get_season_id__(df)
        return df
        

    
