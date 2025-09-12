from .endpoint import Endpoint

class BoxScoreAdvanced(Endpoint):
    def __init__(self, end_period=14, end_range=0, game_id='0021700807', range_type=0, start_period=1, start_range=0, user_agent=None):
        params = {
            'EndPeriod': end_period,
            'EndRange': end_range,
            'GameID': game_id,
            'RangeType': range_type,
            'StartPeriod': start_period,
            'StartRange': start_range,
        }
        super().__init__(endpoint="boxscoreadvancedv3", params=params, user_agent=user_agent)
    