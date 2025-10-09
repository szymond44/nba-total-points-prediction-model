from .endpoint import Endpoint


class PlayerDashboard(Endpoint):
    """
    Represents an API endpoint for retrieving game-by-game player statistics.
    
    Returns individual game logs with columns like:
    - SEASON_ID, PLAYER_ID, PLAYER_NAME, NICKNAME, TEAM_ID, TEAM_ABBREVIATION
    - GAME_ID, GAME_DATE, MATCHUP, WL (Win/Loss)
    - MIN, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT
    - FTM, FTA, FT_PCT, OREB, DREB, REB
    - AST, TOV, STL, BLK, BLKA, PF, PFD, PTS
    - PLUS_MINUS, VIDEO_AVAILABLE
    
    Example usage:
        # Get all player game logs for 2024-25 season
        endpoint = PlayerDashboard(season="2024-25")
        df = endpoint.get_dataframe()
        
        # Get specific player's game logs
        endpoint = PlayerDashboard(season="2024-25", player_id="2544")
        df = endpoint.get_dataframe()
        
        # Get game logs for date range
        endpoint = PlayerDashboard(
            season="2024-25",
            date_from="2024-10-01",
            date_to="2024-12-31"
        )
        df = endpoint.get_dataframe()
    """
    
    def __init__(
        self,
        season="2024-25",
        season_type="Regular Season",
        player_id=None,
        team_id=None,
        date_from="",
        date_to="",
        league_id="00",
        outcome="",
        location="",
        month=0,
        season_segment="",
        vs_conference="",
        vs_division="",
        opponent_team_id=0,
        po_round=0,
        last_n_games=0,
    ):
        """
        Initialize the PlayerDashboard endpoint for game-by-game stats.
        
        Args:
            season (str): Season in 'YYYY-YY' format (e.g., '2024-25')
            season_type (str): 'Regular Season', 'Playoffs', 'All Star', 'Pre Season'
            player_id (str, optional): Specific player ID to filter by
            team_id (str, optional): Specific team ID to filter by
            date_from (str): Start date in 'MM/DD/YYYY' format
            date_to (str): End date in 'MM/DD/YYYY' format
            league_id (str): '00' for NBA, '10' for WNBA, '20' for G League
            outcome (str): 'W' for wins only, 'L' for losses only, '' for all
            location (str): 'Home' or 'Road', '' for all
            month (int): Month number (0 for all, 1-12 for specific month)
            season_segment (str): 'Pre All-Star', 'Post All-Star', '' for all
            vs_conference (str): 'East', 'West', '' for all
            vs_division (str): Division name or '' for all
            opponent_team_id (int): Specific opponent team ID or 0 for all
            po_round (int): Playoff round (0 for all)
            last_n_games (int): Last N games to retrieve (0 for all)
        """
        params = {
            "DateFrom": date_from,
            "DateTo": date_to,
            "GameSegment": "",
            "ISTRound": "",
            "LastNGames": last_n_games,
            "LeagueID": league_id,
            "Location": location,
            "MeasureType": "Base",
            "Month": month,
            "OpponentTeamID": opponent_team_id,
            "Outcome": outcome,
            "PORound": po_round,
            "PaceAdjust": "N",
            "PerMode": "Totals",  # Per game stats are the raw totals per game
            "Period": 0,
            "PlusMinus": "N",
            "Rank": "N",
            "Season": season,
            "SeasonSegment": season_segment,
            "SeasonType": season_type,
            "ShotClockRange": "",
            "VsConference": vs_conference,
            "VsDivision": vs_division,
        }
        
        # Add optional filters
        if player_id is not None:
            params["PlayerID"] = player_id
        if team_id is not None:
            params["TeamID"] = team_id
            
        super().__init__(endpoint="playergamelogs", params=params)