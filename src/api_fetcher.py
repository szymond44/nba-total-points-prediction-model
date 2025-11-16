from typing import Literal

import pandas as pd
import requests


class ApiFetcher:
    """
    API client for handling middle-tier API endpoints.

    Provides a clean interface for fetching NBA data from the local API server
    that serves as a middleware between the application and external NBA APIs.
    """

    BASE_URL = "127.0.0.1:8000/api/"

    def __init__(self, starting_year, ending_year):
        self.starting_year = starting_year
        self.ending_year = ending_year

    def get_dataframe(
        self, endpoint: Literal["leaguegamelog", "playergamelogs/all"] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Fetches data from the specified API endpoint and returns it as a pandas DataFrame.
        Args:
            endpoint (Literal["leaguegamelog"], optional):
                The API endpoint to fetch data from. Must be specified.
            **kwargs:
                Additional query parameters to include in the API request.
        Returns:
            pd.DataFrame:
                DataFrame containing the data returned from the API.
        Raises:
            ValueError:
                If the endpoint is not specified.
            requests.HTTPError:
                If the API request fails (status code is not 200).
        """
        if endpoint is None:
            raise ValueError("Endpoint must be specified")

        url = f"http://{self.BASE_URL}{endpoint}"
        params = {
            "starting_year": self.starting_year,
            "ending_year": self.ending_year,
            **kwargs,
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            raise requests.HTTPError(
                f"API request failed with status code {response.status_code}"
            )

        data = response.json()
        return pd.DataFrame(data)
