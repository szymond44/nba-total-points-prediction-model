from abc import ABC
from typing import Any, Dict, List

import pandas as pd

from ..fetcher import Fetcher


class Endpoint(ABC):
    """
    Abstract base class for API endpoints.

    This class provides a template for interacting with API endpoints, fetching data, and returning results in different formats.

    Attributes:
        __endpoint (str): The API endpoint URL or identifier.
        __params (dict): Parameters to be sent with the API request.
        __api (Fetcher): Instance of the Fetcher class used to perform API requests.
        __user_agent (Dict[str, str], optional): Custom user agent headers for the API request.

    Methods:
        get_json() -> List[Dict[str, Any]]:
            Fetches data from the API and returns it as a list of dictionaries (JSON-like records).
            Raises RuntimeError if no data is returned.

        get_dataframe() -> pd.DataFrame:
            Fetches data from the API and returns it as a pandas DataFrame.
            Raises RuntimeError if no data is returned.

    Raises:
        ValueError: If endpoint or params are not provided during initialization.
        RuntimeError: If the API fetch returns no data.
    """

    def __init__(self, endpoint: str, params: dict, user_agent: Dict[str, str] = None):
        if not endpoint or not params:
            raise ValueError("Endpoint and params must be provided")
        self.__endpoint = endpoint
        self.__params = params
        self.__api = Fetcher()
        self.__user_agent = user_agent

    def get_json(self) -> List[Dict[str, Any]]:
        """
        Fetches data from the API endpoint and returns it as a list of dictionaries.

        Returns:
            List[Dict[str, Any]]: The fetched data, where each dictionary represents a record.

        Raises:
            RuntimeError: If no data is returned from the API.
        """
        data: pd.DataFrame = self.__api.fetch(self.__endpoint, self.__params)
        if data.empty:
            raise RuntimeError("Failed to fetch data from the API")
        return data.to_dict(orient="records")

    def get_dataframe(self) -> pd.DataFrame:
        """
        Fetches data from the API and returns it as a pandas DataFrame.

        Returns:
            pd.DataFrame: The data retrieved from the API.

        Raises:
            RuntimeError: If the fetched data is empty.
        """
        data: pd.DataFrame = self.__api.fetch(
            self.__endpoint, self.__params, user_agent=self.__user_agent
        )
        if data.empty:
            raise RuntimeError("Failed to fetch data from the API")
        return data
