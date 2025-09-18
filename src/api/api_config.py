from dataclasses import dataclass


@dataclass(frozen=True)
class ApiConfig:
    """
    ApiConfig is a configuration class for interacting with the NBA stats API.
    Attributes:
        BASE_URL (str): The base URL for the NBA stats API endpoints.
        RESPONSE_HEADERS (dict): Default HTTP headers used for API requests to mimic a browser and ensure proper responses.
        REQUEST_TIMEOUT (int): Timeout duration (in seconds) for API requests.
        MINIMAL_YEAR (int): The earliest year supported for data queries.
        MAXIMAL_YEAR (int): The latest year supported for data queries.
    Note:
        This class is not intended to be instantiated. Attempting to instantiate will raise a RuntimeError.
    """
    BASE_URL = "https://stats.nba.com/stats/"
    RESPONSE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Host": "stats.nba.com",
        "Referer": "https://www.nba.com/",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
    }
    REQUEST_TIMEOUT = 60

    MINIMAL_YEAR = 1980
    MAXIMAL_YEAR = 2050

    def __init__(self):
        raise RuntimeError("This class should not be instantiated")
