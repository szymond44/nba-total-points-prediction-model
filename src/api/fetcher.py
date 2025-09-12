from .api_config import ApiConfig
import requests
import pandas as pd

class Fetcher:
    def __init__(self):
        self.__base_url__  = ApiConfig.BASE_URL
        self.__headers__ = ApiConfig.RESPONSE_HEADERS
        self.__timeout__ = ApiConfig.REQUEST_TIMEOUT

    def fetch(self, endpoint: str, params: dict, user_agent=None) -> pd.DataFrame:
        url = f"{self.__base_url__ }{endpoint}"
        self.__headers__['User-Agent'] = user_agent or self.__headers__['User-Agent']
        try: 
            response = requests.get(
                url=url, 
                headers=self.__headers__, 
                params=params, 
                timeout=30
            )

            response.raise_for_status()
            data = response.json()
            
            # New structure
            if 'boxScoreAdvanced' in data:
                boxscore_advanced = data['boxScoreAdvanced']
                df = pd.DataFrame(boxscore_advanced).fillna(0)
                return df
            
            # Old structure
            elif 'resultSets' in data and data['resultSets']:
                result_set = data['resultSets'][0]
                headers = result_set.get('headers', [])
                rows = result_set.get('rowSet', [])
                df = pd.DataFrame(rows, columns=headers)
                df = df.fillna(0)
                return df

    
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return pd.DataFrame()
        except (KeyError, ValueError) as e:
            print(f"Invalid response format: {e}")
            return pd.DataFrame()