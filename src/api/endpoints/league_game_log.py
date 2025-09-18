from .endpoint import Endpoint


class LeagueGameLog(Endpoint):
    """
    Represents an API endpoint for retrieving league game logs.

    Args:
        counter (int, optional): Number of records to return. Defaults to 10.
        season (str, optional): Season year in 'YYYY-YY' format. Defaults to '2024-25'.
        season_type (str, optional): Type of season ('Regular Season', 'Playoffs', etc.). Defaults to 'Regular Season'.
        sorter (str, optional): Field to sort results by. Defaults to 'DATE'.
        date_from (str, optional): Start date filter in 'YYYY-MM-DD' format. Defaults to '' (no filter).
        date_to (str, optional): End date filter in 'YYYY-MM-DD' format. Defaults to '' (no filter).
        league_id (str, optional): League identifier. Defaults to '00'.
        player_or_team (str, optional): Specify 'T' for team or 'P' for player. Defaults to 'T'.
        direction (str, optional): Sort direction ('ASC' or 'DESC'). Defaults to 'DESC'.

    Initializes the endpoint with the provided parameters for querying league game logs.
    """

    def __init__(
        self,
        counter=10,
        season="2024-25",
        season_type="Regular Season",
        sorter="DATE",
        date_from="",
        date_to="",
        league_id="00",
        player_or_team="T",
        direction="DESC",
    ):
        params = {
            "Counter": counter,
            "DateFrom": date_from,
            "DateTo": date_to,
            "Direction": direction,
            "LeagueID": league_id,
            "PlayerOrTeam": player_or_team,
            "Season": season,
            "SeasonType": season_type,
            "Sorter": sorter,
        }
        super().__init__(endpoint="leaguegamelog", params=params)
