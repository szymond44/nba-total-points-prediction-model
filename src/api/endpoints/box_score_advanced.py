from .endpoint import Endpoint


class BoxScoreAdvanced(Endpoint):
    """
    Represents the NBA stats API endpoint for advanced box score statistics of a specific game.

    Args:
        end_period (int, optional): The last period to include in the stats. Defaults to 14.
        end_range (int, optional): The ending range for stats collection. Defaults to 0.
        game_id (str, optional): The unique identifier for the NBA game. Defaults to '0021700807'.
        range_type (int, optional): The type of range for stats collection. Defaults to 0.
        start_period (int, optional): The first period to include in the stats. Defaults to 1.
        start_range (int, optional): The starting range for stats collection. Defaults to 0.
        user_agent (str, optional): Custom user agent string for the API request. Defaults to None.

    Example:
        box_score = BoxScoreAdvanced(game_id='0021700807')
    """

    def __init__(
        self,
        end_period=14,
        end_range=0,
        game_id="0021700807",
        range_type=0,
        start_period=1,
        start_range=0,
        user_agent=None,
    ):
        params = {
            "EndPeriod": end_period,
            "EndRange": end_range,
            "GameID": game_id,
            "RangeType": range_type,
            "StartPeriod": start_period,
            "StartRange": start_range,
        }
        super().__init__(
            endpoint="boxscoreadvancedv3", params=params, user_agent=user_agent
        )
