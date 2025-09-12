from typing import Literal
import requests
import pandas as pd

class ApiFetcher:
    """
    API client for handling middle-tier API endpoints.
    
    Provides a clean interface for fetching NBA data from the local API server
    that serves as a middleware between the application and external NBA APIs.
    """
    
    BASE_URL = "127.0.0.1:8000/api/"

    def __init__(self, starting_year, ending_year):
        self.__starting_year = starting_year
        self.__ending_year = ending_year
    
    def get_dataframe(self, endpoint: Literal["leaguegamelog", "boxscoreadvanced"] = None):
        if endpoint is None:
            raise ValueError("Endpoint must be specified")
            
        url = f"http://{self.BASE_URL}{endpoint}"
        params = {
            "starting_year": self.__starting_year,
            "ending_year": self.__ending_year
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")
            
        data = response.json()
        return pd.DataFrame(data)