import pandas as pd
import requests

from .api_config import ApiConfig


class Fetcher:
    """
    Fetcher is a class responsible for retrieving data from a specified API endpoint and returning it as a pandas DataFrame.
    Attributes:
        __base_url__ (str): The base URL for the API requests, sourced from ApiConfig.
        __headers__ (dict): The headers to include in API requests, sourced from ApiConfig.
        __timeout__ (int): The timeout value for API requests, sourced from ApiConfig.
    Methods:
        fetch(endpoint: str, params: dict, user_agent=None) -> pd.DataFrame:
            Sends a GET request to the specified API endpoint with provided parameters and optional user agent.
            Handles two possible response structures:
                - If "boxScoreAdvanced" is present, returns its data as a DataFrame.
                - If "resultSets" is present, returns the first result set as a DataFrame.
            Fills missing values with 0.
            Returns an empty DataFrame if the request fails or the response format is invalid.
    """

    def __init__(self):
        self.__base_url__ = ApiConfig.BASE_URL
        self.__headers__ = ApiConfig.RESPONSE_HEADERS
        self.__timeout__ = ApiConfig.REQUEST_TIMEOUT

    def fetch(self, endpoint: str, params: dict, user_agent=None) -> pd.DataFrame:
        """
        Fetches data from a specified API endpoint and returns it as a pandas DataFrame.
        Args:
            endpoint (str): The API endpoint to fetch data from.
            params (dict): Query parameters to include in the request.
            user_agent (str, optional): Custom User-Agent header value. If not provided, uses the default.
        Returns:
            pd.DataFrame: DataFrame containing the fetched data. Returns an empty DataFrame if the request fails or the response format is invalid.
        Raises:
            None: Exceptions are caught and handled internally, with errors printed to stdout.
        """
        url = f"{self.__base_url__ }{endpoint}"
        self.__headers__["User-Agent"] = user_agent or self.__headers__["User-Agent"]
        try:
            response = requests.get(
                url=url, headers=self.__headers__, params=params, timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # New structure
            if "boxScoreAdvanced" in data:
                boxscore_advanced = data["boxScoreAdvanced"]
                df = pd.DataFrame(boxscore_advanced).fillna(0)
                return df

            # Old structure
            elif "resultSets" in data and data["resultSets"]:
                result_set = data["resultSets"][0]
                headers = result_set.get("headers", [])
                rows = result_set.get("rowSet", [])
                df = pd.DataFrame(rows, columns=headers)
                df = df.fillna(0)
                return df

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return pd.DataFrame()
        except (KeyError, ValueError) as e:
            print(f"Invalid response format: {e}")
            return pd.DataFrame()
