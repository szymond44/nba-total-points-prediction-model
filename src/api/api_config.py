from dataclasses import dataclass

@dataclass(frozen=True)
class ApiConfig:
    BASE_URL = "https://stats.nba.com/stats/"
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
    REQUEST_TIMEOUT = 60 

    MINIMAL_YEAR = 1980
    MAXIMAL_YEAR = 2050

    def __init__(self):
        raise RuntimeError("This class should not be instantiated")
    