from abc import ABC
from typing import Any, Dict, List


class DataProcessing(ABC):
    def __init__(self, **kwargs):
        self.__data__: List[Dict[str, Any]] = None
    def get_json(self) -> List[Dict[str, Any]]:
        if self.__data__ is None:
            self.__data__ = self.__process_data__()
        return self.__data__
    
    def __process_data__(self):
        raise NotImplementedError("Subclasses must implement this method")