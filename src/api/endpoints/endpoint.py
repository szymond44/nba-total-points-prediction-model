from abc import ABC
from typing import List, Dict, Any
from ..fetcher import Fetcher
import pandas as pd

class Endpoint(ABC):
    def __init__(self, endpoint: str, params: dict, user_agent: Dict[str, str] = None):
        if not endpoint or not params:
            raise ValueError("Endpoint and params must be provided")
        self.__endpoint = endpoint
        self.__params = params
        self.__api = Fetcher()
        self.__user_agent = user_agent
    def get_json(self) -> List[Dict[str, Any]]:
        data: pd.DataFrame = self.__api.fetch(self.__endpoint, self.__params)
        if data.empty:
            raise RuntimeError("Failed to fetch data from the API")
        return data.to_dict(orient='records')
    def get_dataframe(self) -> pd.DataFrame:
        data: pd.DataFrame = self.__api.fetch(self.__endpoint, self.__params, user_agent=self.__user_agent)
        if data.empty:
            raise RuntimeError("Failed to fetch data from the API")
        return data